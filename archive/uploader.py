import psycopg2
import json
import os

DB_URL = # here was the url

def main():
	# open("data.json") opened wrong directory for some reason
	with open(os.path.dirname(os.path.realpath(__file__)) + "/data.json") as file:
		data = json.load(file)
	with psycopg2.connect(DB_URL, sslmode="require") as c:
		cur = c.cursor()
		for i, title in enumerate(data['fact_titles']):
			cur.execute(f"INSERT INTO facts(gapless_id, title) "
						f"VALUES('{i + 1}', %s)", [title])
		for i, q in enumerate(data['chgks']):
			cur.execute("INSERT INTO chgks(gapless_id, title, text, answer, "
						"author, send_stats, tried, answered, published) "
						f"VALUES({i+1}, %s, %s, %s,"
						f"{q['author']}, {q['getstat']}, {q['tried']}, "
						f"{q['answered']}, TRUE)", [q['title'], q['text'],
													q['answer']])
		for i, q in enumerate(data['svoyaks']):
			cur.execute("INSERT INTO svoyaks(gapless_id, title, text, answer, "
						"author, send_stats, tried, published, keys) "
						f"VALUES({i+1}, %s, %s, %s,"
						f"{q['author']}, {q['getstat']}, {q['tried']}, "
						f"TRUE, %s)", [q['title'], q['text'], q['answer'],
									   q['keys']])


if __name__ == "__main__":
	main()
