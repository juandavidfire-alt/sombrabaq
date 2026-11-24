-- SombraBAQ - revision previa de RLS
-- SOLO LECTURA: este archivo consulta el esquema y los permisos actuales.
-- No crea ni modifica tablas, politicas, funciones, permisos o datos.
-- Ejecutar estas consultas en SQL Editor solo para recopilar evidencia.
-- No aplicar politicas hasta verificar el esquema, los grants y los flujos
-- de moderacion/canje del proyecto Supabase concreto.

-- Modelo de acceso propuesto; requiere validacion antes de convertirlo en DDL:
-- admins: cada usuario solo puede consultar su propia pertenencia; las altas y
--         bajas se administran fuera del cliente publico.
-- perfiles: lectura y actualizacion solo del perfil propio; limitar las
--            columnas actualizables para impedir cambios de privilegios.
-- publicaciones: lectura publica; insercion autenticada solo con user_id propio;
--                eliminacion reservada a moderacion.
-- cupones: lectura publica de cupones activos; escritura solo administrativa.
-- canjes: lectura solo del propietario; sin escrituras directas desde el cliente.
--         El RPC canjear debe validar y descontar saldo/stock atomicamente.
-- reportes: lectura propia y lectura publica minimizada; insercion autenticada
--           como pendiente; transiciones solo mediante moderacion autorizada.
-- moderacion_log: lectura solo administrativa; escrituras mediante una ruta
--                 transaccional y autorizada, no desde el cliente.
-- storage.objects: subida solo a la carpeta del usuario y lectura publica solo
--                  de evidencias aprobadas, como en la politica existente.
-- La RLS de filas no oculta columnas. No exponer coordenadas exactas, user_id,
-- notas privadas ni rutas de evidencia mediante una consulta publica amplia.

-- 1. Estado de RLS en las tablas usadas por la aplicacion.
with target_tables(table_name) as (
    values
        ('admins'),
        ('perfiles'),
        ('publicaciones'),
        ('cupones'),
        ('canjes'),
        ('reportes'),
        ('moderacion_log')
)
select
    target_tables.table_name,
    coalesce(pg_class.relrowsecurity, false) as rls_enabled,
    coalesce(pg_class.relforcerowsecurity, false) as rls_forced,
    pg_class.relkind as relation_kind
from target_tables
left join pg_namespace
    on pg_namespace.nspname = 'public'
left join pg_class
    on pg_class.relnamespace = pg_namespace.oid
    and pg_class.relname = target_tables.table_name
    and pg_class.relkind in ('r', 'p')
order by target_tables.table_name;

-- 2. Columnas y tipos reales; confirmar que coinciden con las politicas
--    propuestas antes de preparar una migracion ejecutable.
select
    table_name,
    column_name,
    data_type,
    is_nullable,
    column_default
from information_schema.columns
where table_schema = 'public'
  and table_name in (
      'admins', 'perfiles', 'publicaciones', 'cupones',
      'canjes', 'reportes', 'moderacion_log'
  )
order by table_name, ordinal_position;

-- 3. Politicas RLS existentes para las tablas relevantes.
select
    schemaname,
    tablename,
    policyname,
    permissive,
    roles,
    cmd,
    qual,
    with_check
from pg_policies
where schemaname = 'public'
  and tablename in (
      'admins', 'perfiles', 'publicaciones', 'cupones',
      'canjes', 'reportes', 'moderacion_log'
  )
order by tablename, policyname;

-- 4. Grants de tabla otorgados a roles de la API.
select
    table_name,
    grantee,
    privilege_type
from information_schema.role_table_grants
where table_schema = 'public'
  and table_name in (
      'admins', 'perfiles', 'publicaciones', 'cupones',
      'canjes', 'reportes', 'moderacion_log'
  )
  and grantee in ('anon', 'authenticated', 'service_role', 'PUBLIC')
order by table_name, grantee, privilege_type;

-- 5. Seguridad y permisos de las funciones llamadas por la aplicacion.
select
    pg_proc.proname as function_name,
    pg_get_function_identity_arguments(pg_proc.oid) as arguments,
    pg_proc.prosecdef as security_definer,
    pg_proc.proconfig is not null as has_function_settings,
    has_function_privilege('anon', pg_proc.oid, 'execute') as anon_can_execute,
    has_function_privilege('authenticated', pg_proc.oid, 'execute') as authenticated_can_execute
from pg_proc
join pg_namespace on pg_namespace.oid = pg_proc.pronamespace
where pg_namespace.nspname = 'public'
  and pg_proc.proname in ('canjear', 'ranking_publico')
order by function_name, arguments;
