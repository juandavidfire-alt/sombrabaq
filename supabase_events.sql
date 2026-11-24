-- SombraBAQ - eventos, inscripciones y puntos por asistencia confirmada.
-- Revisar antes de ejecutar en el SQL Editor del proyecto Supabase.
-- Este archivo crea objetos y cambia permisos/RLS; no lo ejecutes sin
-- confirmar que el esquema objetivo y la tabla public.admins coinciden.

begin;

create table if not exists public.eventos_comunitarios (
    id bigint generated always as identity primary key,
    titulo text not null check (char_length(btrim(titulo)) between 5 and 120),
    descripcion text not null check (char_length(btrim(descripcion)) between 10 and 1200),
    lugar text not null check (char_length(btrim(lugar)) between 3 and 200),
    fecha timestamptz not null,
    puntos integer not null check (puntos between 1 and 500),
    cupos integer not null check (cupos between 1 and 10000),
    estado text not null default 'borrador'
        check (estado in ('borrador', 'publicado', 'cancelado', 'finalizado')),
    creado_por uuid not null references auth.users(id),
    creado_at timestamptz not null default now()
);

create index if not exists eventos_comunitarios_publicados_fecha_idx
    on public.eventos_comunitarios (fecha)
    where estado = 'publicado';

create table if not exists public.asistencias_eventos (
    id bigint generated always as identity primary key,
    evento_id bigint not null references public.eventos_comunitarios(id) on delete restrict,
    usuario_id uuid not null references auth.users(id) on delete cascade,
    estado text not null default 'pendiente'
        check (estado in ('pendiente', 'confirmada', 'rechazada')),
    registrado_at timestamptz not null default now(),
    verificado_por uuid references auth.users(id),
    verificado_at timestamptz,
    razon_verificacion text,
    unique (evento_id, usuario_id),
    check (
        (estado = 'pendiente' and verificado_por is null and verificado_at is null)
        or (estado in ('confirmada', 'rechazada') and verificado_por is not null and verificado_at is not null)
    )
);

create index if not exists asistencias_eventos_usuario_estado_idx
    on public.asistencias_eventos (usuario_id, estado);

create index if not exists asistencias_eventos_pendientes_idx
    on public.asistencias_eventos (registrado_at)
    where estado = 'pendiente';

create table if not exists public.asistencias_eventos_log (
    id bigint generated always as identity primary key,
    asistencia_id bigint not null references public.asistencias_eventos(id) on delete restrict,
    moderador_id uuid not null references auth.users(id),
    accion text not null check (accion in ('confirmar', 'rechazar')),
    razon text,
    creado_at timestamptz not null default now()
);

create or replace function public.es_admin_sombrabaq()
returns boolean
language sql
stable
security definer
set search_path = pg_catalog, public, auth
as $$
    select exists (
        select 1
        from public.admins
        where user_id = auth.uid()
    );
$$;

revoke all on function public.es_admin_sombrabaq() from public;
grant execute on function public.es_admin_sombrabaq() to anon, authenticated;

alter table public.eventos_comunitarios enable row level security;
alter table public.asistencias_eventos enable row level security;
alter table public.asistencias_eventos_log enable row level security;

drop policy if exists "Eventos publicados visibles" on public.eventos_comunitarios;
create policy "Eventos publicados visibles"
on public.eventos_comunitarios for select
to anon, authenticated
using (estado = 'publicado' or public.es_admin_sombrabaq());

drop policy if exists "Usuarios y admins leen asistencias" on public.asistencias_eventos;
create policy "Usuarios y admins leen asistencias"
on public.asistencias_eventos for select
to authenticated
using (auth.uid() = usuario_id or public.es_admin_sombrabaq());

drop policy if exists "Admins leen auditoria de asistencias" on public.asistencias_eventos_log;
create policy "Admins leen auditoria de asistencias"
on public.asistencias_eventos_log for select
to authenticated
using (public.es_admin_sombrabaq());

revoke all on public.eventos_comunitarios from public, anon, authenticated;
revoke all on public.asistencias_eventos from public, anon, authenticated;
revoke all on public.asistencias_eventos_log from public, anon, authenticated;

grant select (id, titulo, descripcion, lugar, fecha, puntos, cupos, estado, creado_at)
    on public.eventos_comunitarios to anon, authenticated;
grant select (id, evento_id, usuario_id, estado, registrado_at, verificado_at, razon_verificacion)
    on public.asistencias_eventos to authenticated;
grant select (id, asistencia_id, accion, razon, creado_at)
    on public.asistencias_eventos_log to authenticated;

create or replace function public.crear_evento_comunitario(
    p_titulo text,
    p_descripcion text,
    p_lugar text,
    p_fecha timestamptz,
    p_puntos integer,
    p_cupos integer
)
returns bigint
language plpgsql
security definer
set search_path = pg_catalog, public, auth
as $$
declare
    nuevo_id bigint;
begin
    if auth.uid() is null or not public.es_admin_sombrabaq() then
        raise exception 'Solo un administrador puede publicar eventos.'
            using errcode = '42501';
    end if;

    if char_length(btrim(coalesce(p_titulo, ''))) not between 5 and 120
       or char_length(btrim(coalesce(p_descripcion, ''))) not between 10 and 1200
       or char_length(btrim(coalesce(p_lugar, ''))) not between 3 and 200
       or p_fecha is null or p_fecha <= now()
       or p_puntos not between 1 and 500
       or p_cupos not between 1 and 10000 then
        raise exception 'Los datos del evento son inválidos o la fecha ya pasó.'
            using errcode = '22023';
    end if;

    insert into public.eventos_comunitarios
        (titulo, descripcion, lugar, fecha, puntos, cupos, estado, creado_por)
    values
        (btrim(p_titulo), btrim(p_descripcion), btrim(p_lugar), p_fecha, p_puntos, p_cupos, 'publicado', auth.uid())
    returning id into nuevo_id;

    return nuevo_id;
end;
$$;

create or replace function public.registrar_asistencia_evento(p_evento_id bigint)
returns bigint
language plpgsql
security definer
set search_path = pg_catalog, public, auth
as $$
declare
    evento public.eventos_comunitarios%rowtype;
    inscritos integer;
    nueva_asistencia bigint;
begin
    if auth.uid() is null then
        raise exception 'Inicia sesión para inscribirte.'
            using errcode = '42501';
    end if;

    select *
    into evento
    from public.eventos_comunitarios
    where id = p_evento_id
      and estado = 'publicado'
      and fecha > now()
    for update;

    if not found then
        raise exception 'El evento no existe, no está publicado o ya comenzó.'
            using errcode = '22023';
    end if;

    select count(*)::integer
    into inscritos
    from public.asistencias_eventos
    where evento_id = evento.id
      and estado in ('pendiente', 'confirmada');

    if inscritos >= evento.cupos then
        raise exception 'El evento ya no tiene cupos disponibles.'
            using errcode = '22023';
    end if;

    insert into public.asistencias_eventos (evento_id, usuario_id)
    values (evento.id, auth.uid())
    on conflict (evento_id, usuario_id) do nothing
    returning id into nueva_asistencia;

    if nueva_asistencia is null then
        raise exception 'Ya tienes una inscripción registrada para este evento.'
            using errcode = '23505';
    end if;

    return nueva_asistencia;
end;
$$;

create or replace function public.verificar_asistencia_evento(
    p_asistencia_id bigint,
    p_accion text,
    p_razon text default null
)
returns void
language plpgsql
security definer
set search_path = pg_catalog, public, auth
as $$
declare
    asistencia public.asistencias_eventos%rowtype;
    nuevo_estado text;
    fecha_evento timestamptz;
begin
    if auth.uid() is null or not public.es_admin_sombrabaq() then
        raise exception 'Solo un administrador puede verificar asistencias.'
            using errcode = '42501';
    end if;

    if p_accion is null or p_accion not in ('confirmar', 'rechazar') then
        raise exception 'La acción debe ser confirmar o rechazar.'
            using errcode = '22023';
    end if;

    select *
    into asistencia
    from public.asistencias_eventos
    where id = p_asistencia_id
    for update;

    if not found or asistencia.estado <> 'pendiente' then
        raise exception 'La inscripción no existe o ya fue verificada.'
            using errcode = '22023';
    end if;

    select fecha
    into fecha_evento
    from public.eventos_comunitarios
    where id = asistencia.evento_id;

    if p_accion = 'confirmar' and fecha_evento > now() then
        raise exception 'La asistencia solo se puede confirmar después de la fecha del evento.'
            using errcode = '22023';
    end if;

    nuevo_estado := case when p_accion = 'confirmar' then 'confirmada' else 'rechazada' end;

    update public.asistencias_eventos
    set estado = nuevo_estado,
        verificado_por = auth.uid(),
        verificado_at = now(),
        razon_verificacion = nullif(left(btrim(coalesce(p_razon, '')), 300), '')
    where id = p_asistencia_id;

    insert into public.asistencias_eventos_log (asistencia_id, moderador_id, accion, razon)
    values (p_asistencia_id, auth.uid(), p_accion, nullif(left(btrim(coalesce(p_razon, '')), 300), ''));
end;
$$;

create or replace function public.puntos_eventos_confirmados()
returns integer
language sql
stable
security definer
set search_path = pg_catalog, public, auth
as $$
    select coalesce(sum(evento.puntos), 0)::integer
    from public.asistencias_eventos asistencia
    join public.eventos_comunitarios evento on evento.id = asistencia.evento_id
    where asistencia.usuario_id = auth.uid()
      and asistencia.estado = 'confirmada';
$$;

create or replace function public.canjear_evento_recompensa(p_cupon_id bigint)
returns text
language plpgsql
security definer
set search_path = pg_catalog, public, auth
as $$
declare
    usuario uuid := auth.uid();
    cupon public.cupones%rowtype;
    saldo_disponible bigint;
    codigo text;
begin
    if usuario is null then
        raise exception 'Inicia sesión para canjear una recompensa.'
            using errcode = '42501';
    end if;

    perform 1
    from auth.users
    where id = usuario
    for update;

    select *
    into cupon
    from public.cupones
    where id = p_cupon_id
      and activo is true
    for update;

    if not found or cupon.stock <= 0 then
        raise exception 'El cupón no está disponible.'
            using errcode = '22023';
    end if;

    select
        coalesce((
            select sum(reporte.puntos)
            from public.reportes reporte
            where reporte.user_id = usuario
              and reporte.estado = 'aprobado'
        ), 0)
        + coalesce((
            select sum(evento.puntos)
            from public.asistencias_eventos asistencia
            join public.eventos_comunitarios evento on evento.id = asistencia.evento_id
            where asistencia.usuario_id = usuario
              and asistencia.estado = 'confirmada'
        ), 0)
        - coalesce((
            select sum(canje.puntos)
            from public.canjes canje
            where canje.user_id = usuario
        ), 0)
    into saldo_disponible;

    if cupon.puntos is null or cupon.puntos <= 0 or saldo_disponible < cupon.puntos then
        raise exception 'No tienes suficientes puntos para este cupón.'
            using errcode = '22023';
    end if;

    codigo := upper(substr(replace(gen_random_uuid()::text, '-', ''), 1, 6));

    insert into public.canjes (user_id, cupon_id, puntos, codigo)
    values (usuario, cupon.id, cupon.puntos, codigo);

    update public.cupones
    set stock = stock - 1
    where id = cupon.id;

    return codigo;
end;
$$;

revoke all on function public.crear_evento_comunitario(text, text, text, timestamptz, integer, integer) from public, anon;
revoke all on function public.registrar_asistencia_evento(bigint) from public, anon;
revoke all on function public.verificar_asistencia_evento(bigint, text, text) from public, anon;
revoke all on function public.puntos_eventos_confirmados() from public, anon;
revoke all on function public.canjear_evento_recompensa(bigint) from public, anon;

grant execute on function public.crear_evento_comunitario(text, text, text, timestamptz, integer, integer) to authenticated;
grant execute on function public.registrar_asistencia_evento(bigint) to authenticated;
grant execute on function public.verificar_asistencia_evento(bigint, text, text) to authenticated;
grant execute on function public.puntos_eventos_confirmados() to authenticated;
grant execute on function public.canjear_evento_recompensa(bigint) to authenticated;

commit;
