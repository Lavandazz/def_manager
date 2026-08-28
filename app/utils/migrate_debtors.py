# migrate_debtors.py
from sqlalchemy.orm import Session

from config.db.models import Case, Debtor, DebtorType


def migrate_debtors(session: Session):
    # Находим все дела, у которых debtor_id ещё не заполнен
    cases = session.query(Case).filter(Case.debtor_id.is_(None)).all()
    
    for case in cases:
        if not case.debtor_name:
            # Если имя пустое, можно пропустить или поставить заглушку
            continue
        
        # Создаём нового должника
        debtor = Debtor(
            type=DebtorType.PHYSICAL,   # или можно анализировать текст, чтобы определить тип
            name=case.debtor_name
            # остальные поля оставляем NULL, их можно заполнить позже
        )
        session.add(debtor)
        session.flush()  # чтобы получить debtor.id
        
        # Привязываем должника к делу
        case.debtor_id = debtor.id
    
    session.commit()
    print(f"Перенесено {len(cases)} записей")

# Использование:
# session = сессия
# migrate_debtors(session)