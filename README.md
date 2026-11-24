# SombraBAQ

Aplicación Streamlit para observación climática, reportes ciudadanos y participación ambiental en Barranquilla.

## Ejecutar

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Configuración

Crear `.streamlit/secrets.toml` con las credenciales de Supabase y, opcionalmente, Anthropic y Google Earth Engine.

No versionar ni compartir el archivo de secretos.

Para desplegar en Streamlit Community Cloud, configura los mismos valores en **Manage app → Settings → Secrets**:

```toml
[supabase]
url = "https://<project-ref>.supabase.co"
anon_key = "<publishable-or-anon-key>"
```

Obtén ambos valores en **Supabase → Project Settings → API**. Sin estos secretos, la aplicación mostrará el panel climático, pero deshabilitará las funciones que dependen de la base de datos y la autenticación.

### Confirmación de correo

El registro usa Supabase Auth. La aplicación puede solicitar el registro y reenvío del correo, pero no controla la entrega SMTP. Para habilitar y diagnosticar la confirmación:

1. En **Authentication → Providers → Email**, activa la confirmación de correo electrónico.
2. En **Authentication → URL Configuration**, configura la URL pública de la aplicación como **Site URL** y añade esa URL a **Redirect URLs**. En desarrollo, añade también la URL local que uses.
3. En **Project Settings → Auth → SMTP Settings** (o la sección **SMTP** disponible en tu proyecto), configura un proveedor SMTP propio, con remitente verificado y credenciales válidas. El correo SMTP predeterminado de Supabase puede tener restricciones de envío y no es adecuado para producción.
4. Revisa **Authentication → Email Templates** y los registros de Auth/SMTP del proyecto. Envía una prueba a una dirección que controles y comprueba también spam/promociones.

La app muestra “solicitud aceptada” cuando Supabase acepta la petición; esto no confirma que el proveedor haya entregado el mensaje. Si se requiere un destino posterior a la confirmación distinto del **Site URL**, configúralo en Supabase y permítelo explícitamente en **Redirect URLs**.

La capa satelital también requiere una cuenta de servicio de Google Earth Engine habilitada y registrada en Cloud:

```toml
[gee_service_account]
client_email = "cuenta-servicio@proyecto.iam.gserviceaccount.com"
private_key = """-----BEGIN PRIVATE KEY-----
PEGA_AQUI_LA_CLAVE_PRIVADA_COMPLETA
-----END PRIVATE KEY-----
"""
project_id = "id-del-proyecto"
```

`private_key` debe ser la clave privada PEM de la cuenta de servicio (no el JSON completo). Registra el proyecto de Google Cloud para Earth Engine, habilita la API de Earth Engine y otorga a la cuenta de servicio acceso al proyecto. Guarda estos secretos solo en Streamlit Cloud; nunca los subas a GitHub ni los compartas en el chat.

Sin esas credenciales, el mapa muestra las mediciones meteorológicas como alternativa y deja la capa satelital deshabilitada.

## Seguridad inicial

`supabase_security.sql` es una migración inicial, no una auditoría completa de todas las tablas. Antes de ejecutarla en un proyecto existente, revisa su esquema, grants y políticas para evitar conflictos o bloquear flujos de la aplicación.

`supabase_rls_proposal.sql` contiene consultas de solo lectura para inspeccionar RLS, columnas, políticas, grants y funciones, además de un modelo de acceso propuesto. No crea ni modifica objetos y no debe tratarse como una migración lista para producción. La configuración real de Supabase debe revisarse antes de preparar o aplicar políticas adicionales.

La migración inicial agrega:

- Hash de evidencia para detectar duplicados.
- Índices de reportes y estado.
- Políticas RLS básicas.
- Campos de trazabilidad para moderación.
- Registro de auditoría de aprobaciones y rechazos.

### Eventos y puntos por asistencia

El flujo de eventos requiere la migración adicional `supabase_events.sql`. Debe revisarse y ejecutarse manualmente en el proyecto Supabase antes de habilitar inscripciones. Crea tablas con RLS y funciones que permiten publicar eventos solo a administradores, registrar una inscripción pendiente y confirmar o rechazar asistencia después de la fecha del evento. Las verificaciones quedan auditadas. Los puntos de evento se incluyen en el saldo y solo cuentan cuando la asistencia está confirmada; una inscripción por sí sola no concede puntos. El RPC `canjear_evento_recompensa` vuelve a comprobar saldo y stock en una transacción e incluye reportes aprobados y asistencias confirmadas.

Después de aplicar la migración, un administrador autenticado puede publicar convocatorias desde **Moderación → Publicar una convocatoria**. Los títulos sugeridos son plantillas, no eventos confirmados; quien publica debe ingresar lugar, fecha, cupos y descripción reales. El mismo panel permite confirmar la asistencia presencial.

La IA de fotografías ofrece orientación visual, no certifica que una siembra ocurrió ni verifica fecha, ubicación o autoría. Todos los reportes ciudadanos quedan pendientes de revisión humana; los puntos se incorporan al saldo tras la aprobación.

Para permitir que usuarios autenticados publiquen eventos con tema y público destinatario, ejecuta también `supabase_eventos_comunidad.sql` después de `supabase_events.sql`. Los eventos comunitarios se publican de inmediato, tienen un límite de tres por cuenta cada 24 horas y asignan 10 puntos solo cuando un administrador confirma la asistencia después del evento; el organizador no puede confirmar su propia asistencia. La migración agrega tres eventos de demostración con fechas relativas, ubicaciones ficticias y cero puntos. Están marcados como DEMO, no son convocatorias reales y no se debe asistir a ellos.
