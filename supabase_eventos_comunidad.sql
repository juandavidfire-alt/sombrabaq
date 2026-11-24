-- SombraBAQ - creación comunitaria de eventos y datos solo para demostración.
-- Ejecutar después de supabase_events.sql en el proyecto Supabase correcto.
-- Los eventos DEMO no son convocatorias reales, no deben atenderse y no
-- permiten acreditar puntos.

begin;

alter table public.eventos_comunitarios
    add column if not exists tema text not null default 'Actividad comunitaria',
    add column if not exists dirigido_a text not null default 'Comunidad general',
    add column if not exists es_demo boolean not null default false;

alter table public.eventos_comunitarios
    drop constraint if exists eventos_comunitarios_puntos_check;

alter table public.eventos_comunitarios
    add constraint eventos_comunitarios_puntos_check check (puntos between 0 and 500);

grant select (id, tema, dirigido_a, es_demo)
    on public.eventos_comunitarios to anon, authenticated;

create or replace function public.crear_evento_usuario(
    p_titulo text,
    p_tema text,
    p_dirigido_a text,
    p_descripcion text,
    p_lugar text,
    p_fecha timestamptz,
    p_cupos integer
)
returns bigint
language plpgsql
security definer
set search_path = pg_catalog, public, auth
as $$
declare
    nuevo_id bigint;
    eventos_recientes integer;
begin
    if auth.uid() is null then
        raise exception 'Inicia sesión para publicar un evento.'
            using errcode = '42501';
    end if;

    perform pg_advisory_xact_lock(hashtext(auth.uid()::text), 0);

    if char_length(btrim(coalesce(p_titulo, ''))) not between 5 and 120
       or char_length(btrim(coalesce(p_tema, ''))) not between 3 and 100
       or char_length(btrim(coalesce(p_dirigido_a, ''))) not between 3 and 120
       or char_length(btrim(coalesce(p_descripcion, ''))) not between 10 and 1200
       or char_length(btrim(coalesce(p_lugar, ''))) not between 3 and 200
       or p_fecha is null or p_fecha <= now()
       or p_cupos not between 1 and 500 then
        raise exception 'Los datos del evento son inválidos o la fecha ya pasó.'
            using errcode = '22023';
    end if;

    select count(*)::integer
    into eventos_recientes
    from public.eventos_comunitarios
    where creado_por = auth.uid()
      and creado_at >= now() - interval '24 hours'
      and es_demo is false;

    if eventos_recientes >= 3 then
        raise exception 'Puedes publicar hasta 3 eventos en un periodo de 24 horas.'
            using errcode = '22023';
    end if;

    insert into public.eventos_comunitarios
        (titulo, tema, dirigido_a, descripcion, lugar, fecha, puntos, cupos, estado, creado_por, es_demo)
    values
        (btrim(p_titulo), btrim(p_tema), btrim(p_dirigido_a), btrim(p_descripcion),
         btrim(p_lugar), p_fecha, 10, p_cupos, 'publicado', auth.uid(), false)
    returning id into nuevo_id;

    return nuevo_id;
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
    evento public.eventos_comunitarios%rowtype;
    nuevo_estado text;
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

    select *
    into evento
    from public.eventos_comunitarios
    where id = asistencia.evento_id;

    if p_accion = 'confirmar' and evento.fecha > now() then
        raise exception 'La asistencia solo se puede confirmar después de la fecha del evento.'
            using errcode = '22023';
    end if;

    if p_accion = 'confirmar' and evento.es_demo then
        raise exception 'Los eventos de demostración no permiten confirmar asistencia ni acreditar puntos.'
            using errcode = '22023';
    end if;

    if p_accion = 'confirmar' and evento.creado_por = auth.uid() then
        raise exception 'El organizador no puede verificar su propia asistencia.'
            using errcode = '42501';
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

revoke all on function public.crear_evento_usuario(text, text, text, text, text, timestamptz, integer)
    from public, anon;
grant execute on function public.crear_evento_usuario(text, text, text, text, text, timestamptz, integer)
    to authenticated;

revoke all on function public.verificar_asistencia_evento(bigint, text, text) from public, anon;
grant execute on function public.verificar_asistencia_evento(bigint, text, text) to authenticated;

with creador_demo as (
    select coalesce(
        (select user_id from public.admins order by user_id limit 1),
        (select id from auth.users order by created_at limit 1)
    ) as user_id
),
eventos_demo(titulo, tema, dirigido_a, descripcion, dias, puntos, cupos) as (
    values
        ('DEMO · Taller de compostaje', 'Compostaje y residuos orgánicos', 'Familias y principiantes',
         'Evento ficticio de demostración. Ejemplo de taller introductorio con separación de residuos y compostaje. No es una convocatoria real; no asistir.', 7, 0, 20),
        ('DEMO · Caminata de observación de árboles', 'Arbolado urbano y biodiversidad', 'Estudiantes y personas interesadas en naturaleza',
         'Evento ficticio de demostración. Ejemplo de recorrido educativo para aprender a observar árboles urbanos. No es una convocatoria real; no asistir.', 14, 0, 25),
        ('DEMO · Laboratorio de reciclaje creativo', 'Reutilización de materiales', 'Jóvenes y comunidad educativa',
         'Evento ficticio de demostración. Ejemplo de actividad creativa sobre reutilización de materiales limpios. No es una convocatoria real; no asistir.', 21, 0, 15)
)
insert into public.eventos_comunitarios
    (titulo, tema, dirigido_a, descripcion, lugar, fecha, puntos, cupos, estado, creado_por, es_demo)
select
    demo.titulo,
    demo.tema,
    demo.dirigido_a,
    demo.descripcion,
    'DEMO · Lugar ficticio (no asistir)',
    now() + make_interval(days => demo.dias),
    demo.puntos,
    demo.cupos,
    'publicado',
    creador_demo.user_id,
    true
from eventos_demo demo
cross join creador_demo
where creador_demo.user_id is not null
  and not exists (
    select 1
    from public.eventos_comunitarios existente
    where existente.titulo = demo.titulo
      and existente.es_demo is true
);

commit;
