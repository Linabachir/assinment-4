"""Minimal KG builder for Assignment 4."""

import os
import sqlite3
from typing import Any

from dotenv import load_dotenv
from neo4j import GraphDatabase

from llm_loader import load_local_llm


load_dotenv()

URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
AUTH = (
    os.getenv("NEO4J_USER", "neo4j"),
    os.getenv("NEO4J_PASSWORD", "password"),
)


def extract_entities(article_number: str, reg_name: str, content: str) -> dict[str, Any]:
    return {
        "rules": [
            {
                "type": "regulation",
                "action": content[:400],
                "result": content,
            }
        ]
    }


def build_fallback_rules(article_number: str, content: str) -> list[dict[str, str]]:
    return [
        {
            "type": "regulation",
            "action": content[:400],
            "result": content,
        }
    ]


def build_graph() -> None:
    sql_conn = sqlite3.connect("ncu_regulations.db")
    cursor = sql_conn.cursor()
    driver = GraphDatabase.driver(URI, auth=AUTH)

    load_local_llm()

    with driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")

        cursor.execute("SELECT reg_id, name, category FROM regulations")
        regulations = cursor.fetchall()
        reg_map: dict[int, tuple[str, str]] = {}

        for reg_id, name, category in regulations:
            reg_map[reg_id] = (name, category)
            session.run(
                "MERGE (r:Regulation {id:$rid}) SET r.name=$name, r.category=$cat",
                rid=reg_id,
                name=name,
                cat=category,
            )

        cursor.execute("SELECT reg_id, article_number, content FROM articles")
        articles = cursor.fetchall()

        rule_counter = 0

        for reg_id, article_number, content in articles:
            reg_name, reg_category = reg_map.get(reg_id, ("Unknown", "Unknown"))

            session.run(
                """
                MATCH (r:Regulation {id: $rid})
                CREATE (a:Article {
                    number:   $num,
                    content:  $content,
                    reg_name: $reg_name,
                    category: $reg_category
                })
                MERGE (r)-[:HAS_ARTICLE]->(a)
                """,
                rid=reg_id,
                num=article_number,
                content=content,
                reg_name=reg_name,
                reg_category=reg_category,
            )

            extracted = extract_entities(article_number, reg_name, content)
            rules = extracted.get("rules", []) or build_fallback_rules(article_number, content)

            for rule in rules:
                action = (rule.get("action") or "").strip()
                result = (rule.get("result") or "").strip()
                rule_type = (rule.get("type") or "regulation").strip()

                if not action or not result:
                    continue

                rule_counter += 1
                rule_id = f"{reg_id}_{article_number}_{rule_counter}"

                session.run(
                    """
                    MATCH (a:Article {
                        number: $article_number,
                        reg_name: $reg_name
                    })
                    CREATE (ru:Rule {
                        rule_id: $rule_id,
                        type: $rule_type,
                        action: $action,
                        result: $result,
                        art_ref: $article_number,
                        reg_name: $reg_name
                    })
                    MERGE (a)-[:CONTAINS_RULE]->(ru)
                    """,
                    article_number=article_number,
                    reg_name=reg_name,
                    rule_id=rule_id,
                    rule_type=rule_type,
                    action=action,
                    result=result,
                )

        session.run(
            """
            CREATE FULLTEXT INDEX article_content_idx IF NOT EXISTS
            FOR (a:Article) ON EACH [a.content]
            """
        )

        session.run(
            """
            CREATE FULLTEXT INDEX rule_idx IF NOT EXISTS
            FOR (r:Rule) ON EACH [r.action, r.result]
            """
        )

        coverage = session.run(
            """
            MATCH (a:Article)
            OPTIONAL MATCH (a)-[:CONTAINS_RULE]->(r:Rule)
            WITH a, count(r) AS rule_count
            RETURN count(a) AS total_articles,
                   sum(CASE WHEN rule_count > 0 THEN 1 ELSE 0 END) AS covered_articles,
                   sum(CASE WHEN rule_count = 0 THEN 1 ELSE 0 END) AS uncovered_articles
            """
        ).single()

        print(
            f"[Coverage] covered={coverage['covered_articles']}/{coverage['total_articles']}, "
            f"uncovered={coverage['uncovered_articles']}"
        )

    driver.close()
    sql_conn.close()


if __name__ == "__main__":
    build_graph()