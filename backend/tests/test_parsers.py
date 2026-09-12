"""
Unit tests for CodeBridge V1 AST and Schema Parsers
"""
import pytest
from backend.app.parsers.prisma_parser import PrismaParser
from backend.app.parsers.sql_parser import SqlParser
from backend.app.parsers.python_parser import PythonParser
from backend.app.parsers.ts_js_parser import TsJsParser
from backend.app.parsers.drizzle_parser import DrizzleParser


def test_prisma_parser():
    sample_prisma = """
    datasource db {
      provider = "postgresql"
      url      = env("DATABASE_URL")
    }

    enum Role {
      USER
      ADMIN
    }

    model User {
      id        Int      @id @default(autoincrement())
      email     String   @unique
      role      Role     @default(USER)
      posts     Post[]
      createdAt DateTime @default(now())
    }

    model Post {
      id       Int    @id @default(autoincrement())
      title    String
      authorId Int
      author   User   @relation(fields: [authorId], references: [id])
    }
    """
    parser = PrismaParser()
    symbols = parser.parse(sample_prisma)
    assert len(symbols) == 3  # User, Post, Role
    names = [s.name for s in symbols]
    assert "User" in names
    assert "Post" in names
    assert "Role" in names

    models = parser.parse_schema_models(sample_prisma)
    assert len(models) == 2
    user_model = next(m for m in models if m.model_name == "User")
    assert any(f["name"] == "email" for f in user_model.fields)


def test_sql_parser():
    sample_sql = """
    CREATE TABLE users (
        id SERIAL PRIMARY KEY,
        username VARCHAR(50) NOT NULL,
        email VARCHAR(100) NOT NULL
    );

    CREATE TABLE orders (
        id SERIAL PRIMARY KEY,
        user_id INT REFERENCES users(id),
        total_amount DECIMAL(10, 2) NOT NULL
    );
    """
    parser = SqlParser()
    symbols = parser.parse(sample_sql)
    assert len(symbols) == 2
    assert symbols[0].name == "users"
    assert symbols[1].name == "orders"

    models = parser.parse_schema_models(sample_sql)
    assert len(models) == 2
    orders_model = next(m for m in models if m.model_name == "orders")
    assert any(r["to_model"] == "users" for r in orders_model.relations)


def test_python_parser():
    sample_python = """
    from fastapi import FastAPI

    app = FastAPI()

    class UserService:
        \"\"\"Handles user lifecycle logic.\"\"\"
        def calculate_credits(self, user_id: int):
            return user_id * 10

    @app.get("/api/users/{user_id}")
    async def get_user_profile(user_id: int):
        \"\"\"Fetches user by id.\"\"\"
        return {"id": user_id}
    """
    parser = PythonParser()
    symbols = parser.parse(sample_python)
    names = [s.name for s in symbols]
    assert "UserService" in names
    assert "UserService.calculate_credits" in names
    assert "get_user_profile" in names

    endpoint_sym = next(s for s in symbols if s.name == "get_user_profile")
    assert endpoint_sym.symbol_type == "endpoint"


def test_ts_js_parser():
    sample_ts = """
    export interface CustomerAccount {
        id: string;
        balance: number;
    }

    export async function chargeCustomer(customerId: string, amount: number) {
        return { success: true };
    }

    export const refundPayment = async (chargeId: string) => {
        return { refunded: true };
    };
    """
    parser = TsJsParser()
    symbols = parser.parse(sample_ts)
    names = [s.name for s in symbols]
    assert "CustomerAccount" in names
    assert "chargeCustomer" in names
    assert "refundPayment" in names


def test_drizzle_parser():
    sample_drizzle = """
    import { pgTable, serial, text, integer } from 'drizzle-orm/pg-core';

    export const customers = pgTable('customers', {
        id: serial('id').primaryKey(),
        name: text('name').notNull(),
        email: text('email').notNull(),
    });

    export const invoices = pgTable('invoices', {
        id: serial('id').primaryKey(),
        customerId: integer('customer_id').references(() => customers.id),
        amount: integer('amount').notNull(),
    });
    """
    parser = DrizzleParser()
    symbols = parser.parse(sample_drizzle)
    assert len(symbols) == 2
    assert symbols[0].name == "customers"
    assert symbols[1].name == "invoices"

    models = parser.parse_schema_models(sample_drizzle)
    assert len(models) == 2
    inv_model = next(m for m in models if m.model_name == "invoices")
    assert any(r["to_model"] == "customers" for r in inv_model.relations)
