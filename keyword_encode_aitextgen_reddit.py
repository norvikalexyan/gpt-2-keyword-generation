import spacy
import csv
import re
from tqdm import tqdm
from random import shuffle, randint

SCHEMA = {"keywords": "<|keywords|>", "title": "<|title|>"}

PRONOUN_LIST = ["I", "Me", "We", "You", "He", "She", "It", "Him", "Her", "Them", "They"]

PRONOUNS = set(PRONOUN_LIST + [x.lower() for x in PRONOUN_LIST])


def encode_keywords_reddit(
    csv_path,
    model="en_core_web_sm",
    keyword_gen_field="title",
    keyword_sep="<|sep|>",
    repeat=3,
    max_keywords=3,
    keyword_length_max=20,
    out_path="csv_encoded.csv",
    end_token="<|endoftext|>",
    schema=SCHEMA,
):

    data_list = []

    with open(csv_path, "r", encoding="utf8", errors="ignore") as f:
        reader = csv.DictReader(f)
        for row in reader:
            data_list.append(row)

    nlp = spacy.load(model)  # load spaCy model

    with open(out_path, "w", encoding="utf8", errors="ignore") as f:
        w = csv.writer(f)
        for row in tqdm(data_list):

            # Generate the keywords using spacy
            # replace smart quotes first for better tokenization
            text = re.sub(
                u"[\u2018\u2019]",
                "'",
                (re.sub(u"[\u201c\u201d]", '"', row[keyword_gen_field])),
            )

            doc = nlp(text)
            keywords_pos = [
                chunk.text
                if chunk.pos_ == "NOUN"
                else chunk.lemma_
                if chunk.pos_ in ["VERB", "ADJ", "ADV"]
                else "I"
                for chunk in doc
                if not chunk.is_stop
            ]

            keywords_ents = [re.sub(" ", "-", chunk.text) for chunk in doc.ents]
            keywords_compounds = [
                chunk.text
                for chunk in doc.noun_chunks
                if len(chunk.text) < keyword_length_max
            ]

            keywords = list(
                set(keywords_pos + keywords_ents + keywords_compounds) - PRONOUNS
            )  # dedupe

            for _ in range(repeat):
                new_keywords = keywords
                shuffle(new_keywords)
                new_keywords = keyword_sep.join(
                    new_keywords[: randint(0, max_keywords)]
                )

                str_enc = (
                    row["subreddit"]
                    + schema["keywords"]
                    + new_keywords
                    + schema["title"]
                    + text
                )

                w.writerow([str_enc])
