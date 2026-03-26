# /assign-reviewers

Slash command para asignar revisores a Pull Requests de GitHub desde Slack.

## Formato

```
/assign-reviewers <PR_URL> <reviewer1> [reviewer2] ...
```

## Revisores

| Tipo | Formato | Ejemplo |
|---|---|---|
| Usuario | `username` | `jorgealvz` |
| Copilot | `copilot` | `copilot` |
| Equipo | `team:slug` | `team:backend` |

## Ejemplos

### Asignar un revisor

```
/assign-reviewers https://github.com/boliviandevs/hospedate-backend/pull/483 jorgealvz
```

### Asignar varios revisores

```
/assign-reviewers https://github.com/boliviandevs/hospedate-backend/pull/483 jorgealvz andrecuellar
```

### Asignar Copilot como revisor

```
/assign-reviewers https://github.com/boliviandevs/hospedate-backend/pull/483 copilot
```

### Combinar Copilot con revisores humanos

```
/assign-reviewers https://github.com/boliviandevs/hospedate-backend/pull/483 copilot jorgealvz
```

### Asignar un equipo

```
/assign-reviewers https://github.com/boliviandevs/hospedate-backend/pull/483 team:frontend
```

### Ver ayuda

```
/assign-reviewers help
```

## Notas

- Los revisores deben ser colaboradores del repositorio
- Los nombres de usuario son los de **GitHub**, no los de Slack
- Copilot requiere que el repositorio tenga GitHub Copilot habilitado
- Se pueden combinar usuarios, equipos y Copilot en un solo comando
