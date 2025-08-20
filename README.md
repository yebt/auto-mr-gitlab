# auto-mr-gitlab

**auto-mr-gitlab** es una herramienta en Python que automatiza el proceso de creación, aprobación y merge de _Merge Requests_ en proyectos de GitLab, además de gestionar el versionado semántico mediante etiquetas (_tags_).

---

## Características principales

- Obtención del último _tag_ del repositorio.
- Conteo automático de _commits_ clasificados como `feat` o `fix`.
- Generación de un nuevo _tag_ basado en el conteo de cambios, siguiendo versionado semántico.
- Creación automática de un _Merge Request_ (MR) entre `development` y `main`.
- Aprobación automática del MR.
- Revisión de conflictos antes del _merge_.
- Realización del _merge_ del MR.
- Creación de una nueva etiqueta (_tag_) post-merge.
- Interfaz visual en terminal con colores y spinners.

## Requisitos

- Python 3.7+
- Token de acceso personal (PAT) de GitLab con permisos para:
  - Crear/leer _Merge Requests_
  - Crear etiquetas (_tags_)
  - Leer el repositorio

## Instalación

1. Clona el repositorio:

```bash
git clone https://github.com/yebt/auto-mr-gitlab.git
cd auto-mr-gitlab
```

2. Instala las dependencias necesarias:

```bash
pip install -r requirements.txt
```

> Las dependencias principales son `requests`, `python-dotenv`, y `halo`.

3. Crea un archivo `.env` en la raíz del proyecto con el siguiente contenido:

```env
GITLAB_TOKEN=tu_token_de_gitlab
GITLAB_PROJECT_ID=tu_id_de_proyecto
```

## Uso

Puedes ejecutar el script directamente:

```bash
python main.py
```

Esto ejecutará todo el proceso de:

- Detectar última versión publicada
- Contar cambios nuevos
- Generar nueva versión
- Crear y aprobar un nuevo MR
- Hacer merge si no hay conflictos
- Etiquetar el código merged

## Opciones disponibles

Actualmente, las opciones de configuración principales son a través del `.env`:

- `GITLAB_TOKEN`: Token de autenticación.
- `GITLAB_PROJECT_ID`: ID del proyecto en GitLab.

Parámetros como `source_branch` y `target_branch` están definidos por defecto como `development` y `main` respectivamente, pero puedes modificar `main.py` si deseas cambiarlos.

## Ejemplo de flujo

```plaintext
[>>] Initializing
[√√] Last tag: v2.18.6
[√√] Commits found: {'fix': 8, 'feat': 4}
[√√] New tag generated v2.22.8
[√√] New MR title generated: Main Release: 28.04.2025 TAG: v2.22.8
[√√] Merge Request created
[√√] Merge Request approved
[√√] Merge Request merged successfully
[√√] New tag created
```

## Estructura principal del código

- `Alert`: Clase utilitaria para imprimir mensajes coloreados en la terminal.
- `GitlabReleaseManager`: Clase principal que maneja toda la interacción con la API de GitLab.

## TODO / Mejoras futuras

- Detectar _breaking changes_ para incrementar la versión mayor (major).
- Parametrizar `source_branch` y `target_branch` vía argumentos.
- Mejorar el manejo de errores y reintentos.
- Agregar opciones de "dry-run".

## Compilar a bundler

```sh
pyinstaller --onefile main.py

```

This create a `./dist/main` executable

## Licencia

Este proyecto está bajo la licencia MIT.

---

## Contribuciones

¡Las contribuciones son bienvenidas! Puedes abrir _issues_ o _pull requests_ para mejoras o correcciones.

---

## Autor

- [@yebt](https://github.com/yebt)

---

> Happy Automerging! :rocket:
