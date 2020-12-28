import psycopg2


class DatabaseReader:
    def __init__(self, db_url):
        self.c = psycopg2.connect(db_url, sslmode="require")

    def __del__(self):
        self.c.close()

    def get_last_publ_id(self, table_name):
        cur = self.c.cursor()
        cur.execute(f"SELECT MAX(gapless_id) FROM {table_name} WHERE "
                    "published = TRUE;")
        return cur.fetchone()[0]

    def prepare_question_for_publication(self, q_id, table_name):
        publ_id = self.get_last_publ_id(table_name) + 1
        cur = self.c.cursor()
        cur.execute(f"SELECT title, text FROM {table_name} WHERE gapless_id ="
                    f" {q_id};")
        row = cur.fetchone()
        return publ_id, row[0], row[1]

    def get_question_data(self, q_id, table_name):
        cur = self.c.cursor()
        cur.execute(f"SELECT * FROM {table_name} WHERE gapless_id = {q_id};")
        return cur.fetchone()

    def publish_new_question(self, table_name):
        new_publ_id = self.get_last_publ_id(table_name) + 1
        cur = self.c.cursor()
        cur.execute(f"UPDATE {table_name} SET published = true WHERE "
                    f"gapless_id = ({new_publ_id});")

    def delete_row(self, row_id, table_name):
        cur = self.c.cursor()
        if table_name == "chgks" or table_name == "svoyaks":
            cur.execute(f"SELECT published FROM {table_name} WHERE "
                        f"gapless_id = {row_id};")
            if cur.fetchone()[0]:
                raise Exception("Опубликованные вопросы не могут быть удалены.")
        cur.execute(f"DELETE FROM {table_name} WHERE gapless_id = {row_id} "
                    f"RETURNING title;")
        title = cur.fetchone()[0]
        cur.execute(f"UPDATE {table_name} SET gapless_id = gapless_id - 1 "
                    f"WHERE gapless_id > {row_id};")
        return title

    def find_title(self, title, table_name):
        cur = self.c.cursor()
        # !! secure from sql injections !!
        cur.execute(f"SELECT title FROM {table_name} WHERE title = %s;",
                    [title])
        return cur.fetchone() is not None

    def set_title(self, q_id, title, table_name):
        cur = self.c.cursor()
        cur.execute(f"UPDATE {table_name} SET title = {title} "
                    f"WHERE gapless_id = {q_id}")

    def add_fact(self, title):
        cur = self.c.cursor()
        cur.execute("SELECT MAX(gapless_id) FROM facts;")
        new_id = cur.fetchone()[0] + 1
        # !! secure from sql injections !!
        cur.execute(f"INSERT INTO facts(gapless_id, title) VALUES('{new_id}', "
                    "%s);", [title])
        return new_id

    def add_question(self, table_name, title, author, content, answer,
                     get_stats):
        cur = self.c.cursor()
        cur.execute(f"SELECT MAX(gapless_id) FROM {table_name};")
        new_id = cur.fetchone()[0]
        if new_id is None:
            new_id = 0
        new_id += 1
        # !! secure from sql injections !!
        cur.execute(f"INSERT INTO {table_name}(gapless_id, author, title, "
                    f"text, answer, get_stats) VALUES('{new_id}', '{author}', "
                    f"%s, %s, %s, '{get_stats}');", [title, content, answer])
        if table_name == "svoyaks":
            cur.execute("UPDATE svoyaks SET keys='{0,0,0,0,0}' WHERE "
                        f"gapless_id={new_id};")
        return new_id

    def get_answer_by_id(self, q_id, table_name):
        cur = self.c.cursor()
        cur.execute(f"SELECT answer FROM {table_name} "
                    f"WHERE gapless_id = {q_id}")
        return cur.fetchone()[0]

    def get_id_by_title(self, title, table_name):
        cur = self.c.cursor()
        # !! secure from sql injections !!
        cur.execute(f"SELECT gapless_id FROM {table_name} WHERE title = %s",
                    [title])
        return cur.fetchone()[0]

    def update_chgk_stats(self, q_id, answered):
        cur = self.c.cursor()
        cur.execute(f"UPDATE chgks SET tried = tried + 1,"
                    f"answered = answered + {answered} "
                    f"WHERE gapless_id = {q_id}")

    def update_svoyak_stats(self, q_id, deltas):
        cur = self.c.cursor()
        cur.execute("UPDATE svoyaks SET tried = tried + 1 "
                    f"WHERE gapless_id = {q_id}")
        for i, delta in enumerate(deltas):
            if delta != 0:
                cur.execute(f"UPDATE svoyaks SET keys[{i}] = keys[{i}] + 1 "
                            f"WHERE gapless_id={q_id}")




"""
# con = psycopg2.connect(database="testdb", user="postgres",
#    password="postgres", port=5433)

with con:
    cur = con.cursor()
    # cur.execute("INSERT INTO chgks VALUES(0, 'chgk title 3', 'text', 'answer', '12345', 0, false)")
    # cur.execute("UPDATE chgks SET tried = tried + 1, answered = answered + 1 WHERE id = (SELECT MAX(id) FROM chgks)")
    cur.execute("SELECT id, title, answered FROM chgks WHERE id = 1")
    ans = cur.fetchall()
    print(ans[0][1])
"""
