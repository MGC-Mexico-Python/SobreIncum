
_cache = {}


def _version(conexion):

    resultado = conexion.consultar(
        'SELECT MAX("Fecha") AS "Fecha" FROM "ReporteGarantias"',
        output="dict",
    )

    return resultado[0]["Fecha"] if resultado else None


def cacheado(func):

    def envoltura(self, *args, **kwargs):

        version = _version(self.conexion)
        clave = (func.__qualname__, args, tuple(sorted(kwargs.items())))

        if clave in _cache and _cache[clave][0] == version:
            return _cache[clave][1]

        resultado = func(self, *args, **kwargs)
        _cache[clave] = (version, resultado)

        return resultado

    envoltura.__name__ = func.__name__

    return envoltura


def limpiar():

    _cache.clear()