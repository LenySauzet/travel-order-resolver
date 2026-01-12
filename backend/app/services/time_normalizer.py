import re
from datetime import datetime, timedelta
from typing import Any

import dateparser


class TimeNormalizer:
    DATEPARSER_SETTINGS = {
        'PREFER_DATES_FROM': 'future',
        'PREFER_DAY_OF_MONTH': 'first',
        'RETURN_AS_TIMEZONE_AWARE': False,
        'RELATIVE_BASE': None,
    }

    VAGUE_EXPRESSIONS = {
        "matin": {"hour": 8, "minute": 0},
        "matinee": {"hour": 9, "minute": 0},
        "midi": {"hour": 12, "minute": 0},
        "apres midi": {"hour": 14, "minute": 0},
        "soir": {"hour": 18, "minute": 0},
        "soiree": {"hour": 19, "minute": 0},
        "nuit": {"hour": 21, "minute": 0},
    }

    # Regex pour les heures simples françaises: "15h", "15h30", "8h45", "à 17h", etc.
    SIMPLE_TIME_PATTERN = re.compile(
        r'(?:a\s+)?(\d{1,2})\s*h\s*(\d{1,2})?',
        re.IGNORECASE
    )

    @classmethod
    def _parse_simple_time(cls, time_expression: str, reference: datetime) -> datetime | None:
        """Parse les expressions d'heure simples comme '15h', '17h30', 'à 8h45'."""
        match = cls.SIMPLE_TIME_PATTERN.search(time_expression)
        if not match:
            return None
        
        hour = int(match.group(1))
        minute = int(match.group(2)) if match.group(2) else 0
        
        # Validation
        if hour > 23 or minute > 59:
            return None
        
        result_dt = reference.replace(
            hour=hour,
            minute=minute,
            second=0,
            microsecond=0
        )
        
        # Si l'heure est passée, prendre le lendemain
        if result_dt < reference:
            result_dt += timedelta(days=1)
        
        return result_dt

    @classmethod
    def normalize(cls, time_expression: str, reference_date: datetime | None = None) -> str | None:
        if not time_expression:
            return None

        reference = reference_date or datetime.now()
        expression_lower = time_expression.lower().strip()
        
        # 1. D'abord essayer les expressions d'heure simples (15h, 17h30, etc.)
        simple_parsed = cls._parse_simple_time(expression_lower, reference)
        if simple_parsed:
            return simple_parsed.isoformat()
        
        # 2. Ensuite les expressions vagues (matin, soir, etc.)
        for vague_term, time_info in cls.VAGUE_EXPRESSIONS.items():
            if vague_term in expression_lower:
                result_dt = reference.replace(
                    hour=time_info["hour"],
                    minute=time_info["minute"],
                    second=0,
                    microsecond=0
                )
                if result_dt < reference:
                    result_dt += timedelta(days=1)
                return result_dt.isoformat()

        # 3. Enfin utiliser dateparser pour les expressions complexes
        settings: dict[str, Any] = cls.DATEPARSER_SETTINGS.copy()
        settings['RELATIVE_BASE'] = reference

        parsed = dateparser.parse(time_expression, languages=['fr'], settings=settings)  # type: ignore

        if parsed:
            return parsed.isoformat()

        return None
