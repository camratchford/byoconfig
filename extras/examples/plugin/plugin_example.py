import sqlite3
from pathlib import Path

from byo_config.sources.base import BaseVariableSource
from byo_config.config import Config


class SQLite3VariableSource(BaseVariableSource):
    """
    A VariableSource that loads data from a SQLite3 database.
    Args:
        db_path (str):
            The path to the SQLite3 database.
        sql_query (str):
            The SQL query to run.
        variable_name (str):
            The name of the variable to be set.
        **kwargs:
            So that interface is consistent with other VariableSource classes.
    """

    def __init__(self, db_path: str, sql_query: str, variable_name: str, **kwargs):
        with sqlite3.connect(db_path):
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute(sql_query)
            data = cursor.fetchall()
            keys = cursor.description
            results = [dict(zip([key[0] for key in keys], row)) for row in data]
            self.set_data({variable_name: results})


if __name__ == "__main__":
    # Create a database

    db_path = "example.db"
    Path(db_path).unlink(missing_ok=True)

    conn = sqlite3.connect(db_path)
    with sqlite3.connect(db_path):
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE example_table (
                id INTEGER PRIMARY KEY,
                name TEXT,
                age INTEGER
            )
            """
        )
        # Populate the database
        cur.execute(
            """
            INSERT INTO example_table (name, age) VALUES
            ('Alice', 25),
            ('Bob', 30),
            ('Charlie', 35)
            """
        )
        conn.commit()

    # Set up the Config object
    sql_query = "SELECT * FROM example_table"
    variable_name = "example_table"
    config = Config(
        var_source_name="SQLite3",
        precedence=1,
    )

    # Include the SQLite3VariableSource, with all it's keyword arguments passed in
    config.include(
        plugin_class=SQLite3VariableSource,
        db_path=db_path,
        sql_query=sql_query,
        variable_name=variable_name,
    )

    print(config.get())
