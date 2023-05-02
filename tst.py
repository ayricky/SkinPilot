import sqlite3


class CS2SkinPrice:
    def __init__(self):
        self.conn = self.init_db_connection("data/cs_items.db")
        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute("SELECT DISTINCT name FROM items")
            self.all_skin_names = [row["name"] for row in cursor.fetchall()]

    def init_db_connection(self, db_path):
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_item_data(self, item, wear=None):
        with self.conn:
            cursor = self.conn.cursor()
            if wear:
                cursor.execute(
                    """
                    SELECT i.raw_name, i.buff_id, i.wear, i.is_stattrak, i.is_souvenir, b.*
                    FROM items i
                    JOIN buff163 b ON i.buff_id = b.buff_id
                    WHERE i.name = ? AND i.wear = ?
                    """,
                    (item, wear),
                )
            else:
                cursor.execute(
                    """
                    SELECT i.raw_name, i.buff_id, i.wear, i.is_stattrak, i.is_souvenir, b.*
                    FROM items i
                    JOIN buff163 b ON i.buff_id = b.buff_id
                    WHERE i.name = ?
                    """,
                    (item,),
                )
            return cursor.fetchall()


def main():
    cs = CS2SkinPrice()
    data = cs.get_item_data("AK-47 | Case Hardened")
    breakpoint()


if __name__ == "__main__":
    main()
