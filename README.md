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

## Seguridad inicial

Ejecutar `supabase_security.sql` en el editor SQL de Supabase. La migración agrega:

- Hash de evidencia para detectar duplicados.
- Índices de reportes y estado.
- Políticas RLS básicas.
- Campos de trazabilidad para moderación.
- Registro de auditoría de aprobaciones y rechazos.
