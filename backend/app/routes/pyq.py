"""
routes/pyq.py
-------------
Endpoints for Previous Year Questions (PYQ) placement repository.
Subjects: aptitude, dsa, oop, os, dbms, cn
"""

import json
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import PYQQuestion
from app.schemas.schemas import PYQOut
from app.utils.auth import get_current_user_email

router = APIRouter(prefix="/pyq", tags=["PYQ Repository"])

VALID_SUBJECTS = {"aptitude", "dsa", "oop", "os", "dbms", "cn"}


@router.get("/{subject}", response_model=List[PYQOut])
def get_pyq(
    subject: str,
    difficulty: str = Query(None, description="Filter by: easy, medium, hard"),
    limit: int = Query(20, ge=1, le=100),
    email: str = Depends(get_current_user_email),
    db: Session = Depends(get_db)
):
    """
    Fetch placement questions for a given subject.
    
    Args:
        subject: One of aptitude | dsa | oop | os | dbms | cn
        difficulty: Optional filter (easy / medium / hard)
        limit: Max number of questions to return (default 20)
    """
    if subject.lower() not in VALID_SUBJECTS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid subject. Choose from: {', '.join(VALID_SUBJECTS)}"
        )

    query = db.query(PYQQuestion).filter(PYQQuestion.subject == subject.lower())
    if difficulty:
        query = query.filter(PYQQuestion.difficulty == difficulty.lower())

    questions = query.limit(limit).all()
    return questions


@router.get("/subjects/list")
def list_subjects(_: str = Depends(get_current_user_email)):
    """List all available PYQ subjects."""
    return {
        "subjects": [
            {"key": "aptitude", "label": "Quantitative Aptitude"},
            {"key": "dsa",      "label": "Data Structures & Algorithms"},
            {"key": "oop",      "label": "Object-Oriented Programming"},
            {"key": "os",       "label": "Operating Systems"},
            {"key": "dbms",     "label": "Database Management Systems"},
            {"key": "cn",       "label": "Computer Networks"},
        ]
    }


def seed_pyq_data(db: Session):
    """
    Seed the database with sample PYQ questions.
    Call this once during startup if table is empty.
    """
    if db.query(PYQQuestion).count() > 0:
        return   # Already seeded

    sample_questions = [
        # ── Aptitude ──────────────────────────────────────────────────────────
        PYQQuestion(subject="aptitude", difficulty="easy",
            question="A train 150m long passes a pole in 15 seconds. What is its speed in km/h?",
            options=json.dumps(["36 km/h", "54 km/h", "72 km/h", "90 km/h"]),
            answer="36 km/h",
            explanation="Speed = Distance/Time = 150/15 = 10 m/s = 10×3.6 = 36 km/h"),
        PYQQuestion(subject="aptitude", difficulty="medium",
            question="Two pipes A and B can fill a tank in 12 and 18 hours. Both are opened together. In how many hours will the tank be full?",
            options=json.dumps(["7.2 hours", "6 hours", "8 hours", "10 hours"]),
            answer="7.2 hours",
            explanation="Combined rate = 1/12 + 1/18 = 5/36. Time = 36/5 = 7.2 hours"),
        PYQQuestion(subject="aptitude", difficulty="hard",
            question="A sum of ₹8000 is invested at 10% compound interest per annum. What is the amount after 3 years?",
            options=json.dumps(["₹10,648", "₹10,600", "₹10,800", "₹11,000"]),
            answer="₹10,648",
            explanation="A = P(1+r/100)^n = 8000 × 1.1^3 = 8000 × 1.331 = ₹10,648"),

        # ── DSA ───────────────────────────────────────────────────────────────
        PYQQuestion(subject="dsa", difficulty="easy",
            question="What is the time complexity of binary search?",
            options=json.dumps(["O(n)", "O(log n)", "O(n log n)", "O(1)"]),
            answer="O(log n)",
            explanation="Binary search halves the search space in each step, giving O(log n) complexity."),
        PYQQuestion(subject="dsa", difficulty="medium",
            question="Which data structure is used to implement a priority queue efficiently?",
            options=json.dumps(["Stack", "Queue", "Heap", "Linked List"]),
            answer="Heap",
            explanation="A binary heap supports O(log n) insert and O(log n) delete-min operations, ideal for priority queues."),
        PYQQuestion(subject="dsa", difficulty="hard",
            question="What is the worst-case time complexity of QuickSort?",
            options=json.dumps(["O(n log n)", "O(n²)", "O(n)", "O(log n)"]),
            answer="O(n²)",
            explanation="When the pivot is always the smallest or largest element (e.g., sorted input with naive pivot), QuickSort degrades to O(n²)."),

        # ── OOP ───────────────────────────────────────────────────────────────
        PYQQuestion(subject="oop", difficulty="easy",
            question="Which OOP concept allows a class to have multiple methods with the same name but different parameters?",
            options=json.dumps(["Inheritance", "Encapsulation", "Polymorphism", "Abstraction"]),
            answer="Polymorphism",
            explanation="Method overloading (compile-time polymorphism) allows same method name with different signatures."),
        PYQQuestion(subject="oop", difficulty="medium",
            question="What is the purpose of a virtual function in C++?",
            options=json.dumps(["Memory management", "Runtime polymorphism", "Constructor chaining", "Data hiding"]),
            answer="Runtime polymorphism",
            explanation="Virtual functions enable dynamic dispatch, allowing derived class methods to be called via base class pointers."),

        # ── OS ────────────────────────────────────────────────────────────────
        PYQQuestion(subject="os", difficulty="easy",
            question="What is a deadlock?",
            options=json.dumps([
                "A process waiting forever due to circular resource dependency",
                "A process using 100% CPU",
                "A memory overflow error",
                "An infinite loop in user code"
            ]),
            answer="A process waiting forever due to circular resource dependency",
            explanation="Deadlock occurs when a set of processes are each waiting for resources held by others in a circular chain."),
        PYQQuestion(subject="os", difficulty="medium",
            question="Which page replacement algorithm suffers from Belady's Anomaly?",
            options=json.dumps(["LRU", "FIFO", "Optimal", "Clock"]),
            answer="FIFO",
            explanation="FIFO can have more page faults with more frames — this counter-intuitive behavior is Belady's Anomaly."),

        # ── DBMS ──────────────────────────────────────────────────────────────
        PYQQuestion(subject="dbms", difficulty="easy",
            question="Which normal form eliminates partial dependencies?",
            options=json.dumps(["1NF", "2NF", "3NF", "BCNF"]),
            answer="2NF",
            explanation="2NF removes partial dependencies where a non-key attribute depends on part of a composite primary key."),
        PYQQuestion(subject="dbms", difficulty="medium",
            question="What does ACID stand for in database transactions?",
            options=json.dumps([
                "Atomicity, Consistency, Isolation, Durability",
                "Access, Control, Integrity, Data",
                "Atomicity, Completeness, Isolation, Distribution",
                "None of the above"
            ]),
            answer="Atomicity, Consistency, Isolation, Durability",
            explanation="ACID properties ensure reliable transaction processing in database systems."),

        # ── CN ────────────────────────────────────────────────────────────────
        PYQQuestion(subject="cn", difficulty="easy",
            question="Which layer of the OSI model is responsible for routing?",
            options=json.dumps(["Physical", "Data Link", "Network", "Transport"]),
            answer="Network",
            explanation="The Network layer (Layer 3) handles logical addressing (IP) and routing of packets between networks."),
        PYQQuestion(subject="cn", difficulty="medium",
            question="What is the difference between TCP and UDP?",
            options=json.dumps([
                "TCP is connection-oriented and reliable; UDP is connectionless and faster",
                "TCP is faster; UDP is reliable",
                "TCP uses IP; UDP does not",
                "No difference"
            ]),
            answer="TCP is connection-oriented and reliable; UDP is connectionless and faster",
            explanation="TCP ensures delivery with handshaking and retransmission. UDP is lightweight with no guarantee of delivery."),
    ]

    db.add_all(sample_questions)
    db.commit()
    print(f"[Seed] Added {len(sample_questions)} PYQ questions.")
