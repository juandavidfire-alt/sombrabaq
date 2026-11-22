-- SombraBAQ - seguridad y trazabilidad inicial
-- Ejecutar en el editor SQL de Supabase.

alter table public.reportes add column if not exists foto_hash text;
alter table public.reportes add column if not exists ia_confianza double precision;
alter table public.reportes add column if not exists ia_detalle text;
alter table public.reportes add column if not exists moderado_por uuid references auth.users(id);
alter table public.reportes add column if not exists moderado_at timestamptz;
alter table public.reportes add column if not exists razon_moderacion text;

create index if not exists reportes_foto_hash_idx on public.reportes(foto_hash);
create index if not exists reportes_estado_idx on public.reportes(estado);
create index if not exists reportes_user_idx on public.reportes(user_id);

alter table public.reportes enable row level security;

drop policy if exists "Reportes publicos aprobados" on public.reportes;
create policy "Reportes publicos aprobados"
on public.reportes for select
to anon, authenticated
using (estado in ('aprobado', 'verificado_ia'));

drop policy if exists "Usuario ve sus reportes" on public.reportes;
create policy "Usuario ve sus reportes"
on public.reportes for select
to authenticated
using (auth.uid() = user_id);

drop policy if exists "Usuario crea reportes" on public.reportes;
create policy "Usuario crea reportes"
on public.reportes for insert
to authenticated
with check (auth.uid() = user_id and estado in ('pendiente', 'verificado_ia'));

create table if not exists public.moderacion_log (
    id bigint generated always as identity primary key,
    reporte_id bigint not null references public.reportes(id) on delete cascade,
    moderador_id uuid not null references auth.users(id),
    accion text not null check (accion in ('aprobar', 'rechazar')),
    razon text,
    created_at timestamptz not null default now()
);

alter table public.moderacion_log enable row level security;

drop policy if exists "Solo moderadores leen auditoria" on public.moderacion_log;
create policy "Solo moderadores leen auditoria"
on public.moderacion_log for select
to authenticated
using (exists (select 1 from public.admins where user_id = auth.uid()));
