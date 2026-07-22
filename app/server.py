import os
from typing import Optional
from fastapi import FastAPI, Query, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

import database

# Initialize Database on startup
database.init_db()

app = FastAPI(
    title="Antigravity Finance API",
    description="Professional Budget Management API",
    version="1.0.0"
)

# Enable CORS for development flexibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic Schemas for Request Validation ---

class TransactionCreate(BaseModel):
    description: str = Field(..., min_length=1, max_length=255, description="Transaction description")
    amount: float = Field(..., gt=0, description="Transaction amount (must be positive)")
    type: str = Field(..., description="Type of transaction (income or expense)")
    category: str = Field(..., min_length=1, max_length=50, description="Transaction category")
    date: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$", description="Transaction date in YYYY-MM-DD format")

    model_config = {
        "json_schema_extra": {
            "example": {
                "description": "Weekly Grocery Shopping",
                "amount": 124.50,
                "type": "expense",
                "category": "Food",
                "date": "2026-06-29"
            }
        }
    }

class GoalUpdate(BaseModel):
    target_amount: float = Field(..., ge=0, description="Target savings amount")
    saved_amount: float = Field(..., ge=0, description="Currently saved amount")

    model_config = {
        "json_schema_extra": {
            "example": {
                "target_amount": 5000.00,
                "saved_amount": 2500.00
            }
        }
    }

# --- API Endpoints ---

@app.get("/api/transactions")
def get_transactions_endpoint(
    search: str = Query("", description="Filter transactions by description"),
    type: str = Query("all", description="Filter by type ('all', 'income', 'expense')"),
    category: str = Query("all", description="Filter by category name")
):
    """Fetches transactions matching search and filter criteria."""
    try:
        transactions = database.get_transactions(search, type, category)
        return transactions
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error querying transactions: {str(e)}"
        )

@app.post("/api/transactions", status_code=status.HTTP_201_CREATED)
def create_transaction_endpoint(payload: TransactionCreate):
    """Adds a new transaction to the database."""
    if payload.type not in ["income", "expense"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transaction type must be 'income' or 'expense'"
        )
    
    try:
        new_id = database.add_transaction(
            description=payload.description,
            amount=payload.amount,
            trans_type=payload.type,
            category=payload.category,
            date_str=payload.date
        )
        return {"success": True, "id": new_id}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating transaction: {str(e)}"
        )

@app.delete("/api/transactions")
def delete_transaction_endpoint(id: int = Query(..., description="ID of the transaction to delete")):
    """Deletes a transaction by ID. Expected by frontend query parameter (?id=X)."""
    try:
        success = database.delete_transaction(id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Transaction with ID {id} not found"
            )
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting transaction: {str(e)}"
        )

@app.get("/api/stats")
def get_stats_endpoint():
    """Retrieves financial dashboard statistics."""
    try:
        stats = database.get_stats()
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error calculating stats: {str(e)}"
        )

@app.get("/api/goals")
def get_goals_endpoint():
    """Gets the active savings goal."""
    try:
        goals = database.get_goals()
        return goals
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving goals: {str(e)}"
        )

@app.post("/api/goals")
def update_goal_endpoint(payload: GoalUpdate):
    """Updates the active savings goal parameters."""
    try:
        database.update_goal(payload.target_amount, payload.saved_amount)
        return {"success": True}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating goal: {str(e)}"
        )

# --- Mount Static Assets (Serve Frontend) ---

PUBLIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "public")

if os.path.exists(PUBLIC_DIR):
    app.mount("/", StaticFiles(directory=PUBLIC_DIR, html=True), name="public")
else:
    print(f"Warning: public directory not found at {PUBLIC_DIR}. Backend will run API-only.")

# Run with Uvicorn when executed directly
if __name__ == "__main__":
    import uvicorn
    PORT = int(os.environ.get("PORT", 8000))
    # In production, use workers and avoid reload=True
    uvicorn.run("server:app", host="0.0.0.0", port=PORT, reload=True)
