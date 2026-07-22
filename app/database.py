import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, Float, CheckConstraint, func
from sqlalchemy.orm import declarative_base, sessionmaker

# Load environment variables from .env file
load_dotenv()

# Determine project directory to store local SQLite database file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB_FILE = os.path.join(BASE_DIR, "finance.db")

# Read DATABASE_URL from environment or fallback to local SQLite
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    DATABASE_URL = f"sqlite:///{DEFAULT_DB_FILE}"
else:
    # SQLAlchemy requires postgresql:// instead of postgres:// (common in Heroku/Render configs)
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Configure SQLAlchemy Engine and Sessionmaker
# For SQLite, enable check_same_thread to prevent cross-thread access errors in FastAPI
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- Database Models ---

class Transaction(Base):
    """Transaction model representing incomes and expenses."""
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    description = Column(String(255), nullable=False)
    amount = Column(Float, nullable=False)
    type = Column(String(10), CheckConstraint("type IN ('income', 'expense')"), nullable=False)
    category = Column(String(50), nullable=False)
    date = Column(String(10), nullable=False) # ISO YYYY-MM-DD format

class Goal(Base):
    """Goal model representing saving goals."""
    __tablename__ = "goals"
    
    id = Column(Integer, primary_key=True, index=True)
    target_amount = Column(Float, nullable=False)
    saved_amount = Column(Float, nullable=False)

# --- Service Functions ---

def init_db():
    """Initializes tables and seeds dummy data if the database is empty."""
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Seed Transactions
        if db.query(Transaction).count() == 0:
            today = datetime.now()
            dummy_transactions = [
                Transaction(
                    description="Monthly Salary",
                    amount=3500.00,
                    type="income",
                    category="Work",
                    date=(today - timedelta(days=5)).strftime("%Y-%m-%d")
                ),
                Transaction(
                    description="Weekly Supermarket",
                    amount=350.25,
                    type="expense",
                    category="Food",
                    date=(today - timedelta(days=4)).strftime("%Y-%m-%d")
                ),
                Transaction(
                    description="Netflix Subscription",
                    amount=55.90,
                    type="expense",
                    category="Entertainment",
                    date=(today - timedelta(days=3)).strftime("%Y-%m-%d")
                ),
                Transaction(
                    description="Freelance UI Design",
                    amount=1200.00,
                    type="income",
                    category="Work",
                    date=(today - timedelta(days=2)).strftime("%Y-%m-%d")
                ),
                Transaction(
                    description="Car Fuel",
                    amount=180.00,
                    type="expense",
                    category="Transportation",
                    date=(today - timedelta(days=2)).strftime("%Y-%m-%d")
                ),
                Transaction(
                    description="Special Dinner Out",
                    amount=120.00,
                    type="expense",
                    category="Food",
                    date=(today - timedelta(days=1)).strftime("%Y-%m-%d")
                ),
                Transaction(
                    description="Electricity Bill",
                    amount=245.50,
                    type="expense",
                    category="Housing",
                    date=today.strftime("%Y-%m-%d")
                )
            ]
            db.add_all(dummy_transactions)
            db.commit()
            
        # Seed Goals
        if db.query(Goal).count() == 0:
            db.add(Goal(target_amount=5000.00, saved_amount=1500.00))
            db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
    finally:
        db.close()

def get_transactions(search="", filter_type="all", filter_category="all"):
    """Fetches transactions with filters and search queries."""
    db = SessionLocal()
    try:
        query = db.query(Transaction)
        
        if search:
            query = query.filter(Transaction.description.ilike(f"%{search}%"))
            
        if filter_type != "all":
            query = query.filter(Transaction.type == filter_type)
            
        if filter_category != "all":
            query = query.filter(Transaction.category == filter_category)
            
        # Order by date descending, then ID descending
        results = query.order_by(Transaction.date.desc(), Transaction.id.desc()).all()
        
        # Serialize database model list to dictionaries
        return [
            {
                "id": t.id,
                "description": t.description,
                "amount": t.amount,
                "type": t.type,
                "category": t.category,
                "date": t.date
            } for t in results
        ]
    finally:
        db.close()

def add_transaction(description, amount, trans_type, category, date_str):
    """Creates a new transaction record."""
    if not date_str:
        date_str = datetime.now().strftime("%Y-%m-%d")
        
    db = SessionLocal()
    try:
        new_trans = Transaction(
            description=description,
            amount=float(amount),
            type=trans_type,
            category=category,
            date=date_str
        )
        db.add(new_trans)
        db.commit()
        db.refresh(new_trans)
        return new_trans.id
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

def delete_transaction(trans_id):
    """Deletes a transaction from the database."""
    db = SessionLocal()
    try:
        transaction = db.query(Transaction).filter(Transaction.id == trans_id).first()
        if transaction:
            db.delete(transaction)
            db.commit()
            return True
        return False
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

def get_stats():
    """Computes total income, expense, net balance and expense by categories."""
    db = SessionLocal()
    try:
        # Sum of Incomes
        total_income = db.query(func.sum(Transaction.amount)).filter(Transaction.type == "income").scalar() or 0.0
        
        # Sum of Expenses
        total_expense = db.query(func.sum(Transaction.amount)).filter(Transaction.type == "expense").scalar() or 0.0
        
        # Expenses Grouped by Category
        categories_query = db.query(
            Transaction.category,
            func.sum(Transaction.amount)
        ).filter(
            Transaction.type == "expense"
        ).group_by(
            Transaction.category
        ).all()
        
        categories = {item[0]: item[1] for item in categories_query}
        net_balance = total_income - total_expense
        
        # Determine database type and scope for frontend reporting
        db_type = "PostgreSQL" if DATABASE_URL.startswith("postgresql") else "SQLite"
        db_scope = "Cloud / External" if DATABASE_URL.startswith("postgresql") else "Local File"
        
        return {
            "total_income": total_income,
            "total_expense": total_expense,
            "net_balance": net_balance,
            "categories": categories,
            "db_type": db_type,
            "db_scope": db_scope
        }
    finally:
        db.close()

def get_goals():
    """Fetches the latest goal or returns default values."""
    db = SessionLocal()
    try:
        goal = db.query(Goal).order_by(Goal.id.desc()).first()
        if goal:
            return {"target_amount": goal.target_amount, "saved_amount": goal.saved_amount}
        return {"target_amount": 0.0, "saved_amount": 0.0}
    finally:
        db.close()

def update_goal(target_amount, saved_amount):
    """Updates the existing goal or inserts a new one."""
    db = SessionLocal()
    try:
        goal = db.query(Goal).order_by(Goal.id.desc()).first()
        if goal:
            goal.target_amount = float(target_amount)
            goal.saved_amount = float(saved_amount)
        else:
            goal = Goal(target_amount=float(target_amount), saved_amount=float(saved_amount))
            db.add(goal)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully at:", DATABASE_URL)
