# Cómo trabajar en este repositorio

## Ramas

| Rama | Rol | Ambiente al que corresponde | Quién escribe |
|---|---|---|---|
| `main` | Producción: lo que está aprobado y estable | prod | Solo por PR desde `staging` (o `hotfix/*`) |
| `staging` | Pruebas / QA: candidata a salir | qa | Solo por PR desde `develop` |
| `develop` | Desarrollo: integra el trabajo del equipo | dev | Por PR desde `feature/*` |
| `feature/<tema>` | Una tarea o funcionalidad, vive pocos días | tu PC (local) | Tú; se borra al fusionarse |
| `hotfix/<tema>` | Corrección urgente de producción | — | Sale de `main`; vuelve a `main` y a `develop` |

Hoy no hay servidores por ambiente: cada rama representa su ambiente y la
configuración vive en los `.env` de cada máquina. Cuando exista CI/CD, cada rama
se desplegará en su ambiente (environments de GitHub `dev`, `qa`, `prod`).

```
feature/x ──PR──► develop ──PR──► staging ──PR──► main
                     ▲                              │
                     └──────── hotfix/y ◄───────────┘
```

## Flujo diario

```bash
git checkout develop && git pull
git checkout -b feature/limites-de-consumo     # nombre corto y en minúsculas
# ... cambios: spec → pruebas → código (ver AGENTS.md) ...
./scripts/run-tests.sh                          # debe terminar en PASÓ
git push -u origin feature/limites-de-consumo
# abrir PR hacia develop
```

Para salir a QA: PR `develop → staging` y ejecutar el plan de
`specs/004-system-integration/` sobre `staging`. Para salir a producción: PR
`staging → main`.

## Reglas

- Nunca commits directos a `main`, `staging` ni `develop`: siempre PR.
- Un PR se fusiona solo si `run-tests` pasa y el spec está actualizado
  (skill `sdd-specs`).
- Mensajes de commit en español, en presente y diciendo qué cambia y por qué.
- Las keys y `.env` nunca se suben (ya están en `.gitignore`).

Recomendado en GitHub (Settings → Branches → Branch protection rules) para
`main`, `staging` y `develop`: "Require a pull request before merging" y, cuando
exista el workflow de CI, "Require status checks to pass".
