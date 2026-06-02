import numpy as np
import pandas as pd


class Calendario:
    """
    Utilidades para manejo de días hábiles usando numpy.busdaycalendar.

    Todas las fechas se manejan internamente como datetime64[D].
    """

    DIAS_INHABILES = np.array([
        '2026-02-02',
        '2026-03-16',
        '2026-04-02',
        '2026-04-03',
        '2026-05-01',
        '2026-09-15',
        '2026-09-16',
        '2026-11-02',
        '2026-11-16',
        '2026-12-24',
        '2026-12-25',
        '2026-12-31',
        '2027-01-01',
        '2027-02-01',
        '2027-03-15',
    ], dtype='datetime64[D]')

    WEEKMASK = '1111100'  # Lunes a viernes


    @classmethod
    def calendario(cls) -> np.busdaycalendar:
        """
        Construye el calendario hábil.
        """

        return np.busdaycalendar(
            holidays=cls.DIAS_INHABILES,
            weekmask=cls.WEEKMASK
        )


    @staticmethod
    def hoy() -> np.datetime64:
        """
        Fecha actual.
        """

        return np.datetime64('today', 'D')


    @classmethod
    def habil(cls, fecha) -> bool:
        """
        Valida si una fecha es hábil.
        """

        fecha = np.datetime64(fecha, 'D')

        return np.is_busday(
            fecha,
            busdaycal=cls.calendario()
        )


    @classmethod
    def inhabil(cls, fecha) -> bool:
        """
        Valida si una fecha es inhábil.
        """

        return not cls.habil(fecha)


    @classmethod
    def dia_habil_anterior(
        cls,
        fecha=None,
        dias: int = 1
    ) -> np.datetime64:
        """
        Retrocede N días hábiles desde una fecha.
        """

        if dias < 0:
            raise ValueError('dias debe ser positivo')

        if fecha is None:
            fecha = cls.hoy()

        fecha = np.datetime64(fecha, 'D')

        return np.busday_offset(
            fecha,
            offsets=-dias,
            roll='backward',
            busdaycal=cls.calendario()
        )


    @classmethod
    def dia_habil_siguiente(
        cls,
        fecha=None,
        dias: int = 1
    ) -> np.datetime64:
        """
        Avanza N días hábiles desde una fecha.
        """

        if dias < 0:
            raise ValueError('dias debe ser positivo')

        if fecha is None:
            fecha = cls.hoy()

        fecha = np.datetime64(fecha, 'D')

        return np.busday_offset(
            fecha,
            offsets=dias,
            roll='forward',
            busdaycal=cls.calendario()
        )


    @classmethod
    def primer_habil_mes(
        cls,
        fecha=None
    ) -> np.datetime64:
        """
        Primer día hábil del mes.
        """

        if fecha is None:
            fecha = cls.hoy()

        fecha = np.datetime64(fecha, 'D')

        primer_dia = (
            fecha
            .astype('datetime64[M]')
            .astype('datetime64[D]')
        )

        return np.busday_offset(
            primer_dia,
            offsets=0,
            roll='forward',
            busdaycal=cls.calendario()
        )


    @classmethod
    def ultimo_habil_mes(
        cls,
        fecha=None
    ) -> np.datetime64:
        """
        Último día hábil del mes.
        """

        if fecha is None:
            fecha = cls.hoy()

        fecha = np.datetime64(fecha, 'D')

        siguiente_mes = (
            fecha.astype('datetime64[M]') + 1
        ).astype('datetime64[D]')

        return np.busday_offset(
            siguiente_mes,
            offsets=-1,
            roll='backward',
            busdaycal=cls.calendario()
        )


    @classmethod
    def diferencia_habil(
        cls,
        fechas: pd.Series,
        restar_uno: bool = True
    ) -> pd.Series:
        """
        Calcula diferencia de días hábiles entre
        fechas consecutivas.
        """

        fechas = (
            pd.to_datetime(fechas)
            .values
            .astype('datetime64[D]')
        )

        diff = np.busday_count(
            fechas[:-1],
            fechas[1:],
            busdaycal=cls.calendario()
        )

        if restar_uno:
            diff -= 1

        diff = np.maximum(diff, 0)

        return pd.Series(
            np.insert(diff, 0, np.nan),
            index=range(len(fechas))
        )