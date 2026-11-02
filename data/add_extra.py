# Adds a second round of DRAFTED training sentences to data/intents.json (safe to run twice).
# Run after make_intents.py:  python data/add_extra.py
import json, os

EXTRA = {
"lowest_month": [
 "pinakamababang presyo ng baka kailan", "which month were cattle prices cheapest",
 "anong buwan bumagsak ang presyo nang pinakamababa", "what month had the smallest price",
 "kailan pinakamurang bumili ng baka", "lowest priced month from january to june",
 "anong buwan ang pinakamababa ang presyo sa 2026", "ano ang pinakamurang buwan",
 "which month is the cheapest to buy", "saang buwan pinakakaunti ang naibenta",
 "least number of cattle sold which month", "kailan pinakamababa ang timbang na na-trade",
 "month with the smallest volume", "pinakamababang buwan para sa kilo",
 "what was the lowest price month last year", "kailan mura ang baka"],
"price_rating": [
 "ngayon ba ay magandang bumili", "worth buying now ba", "mahal ba ang baka ngayon",
 "is cattle expensive right now", "magandang magbenta ngayong buwan",
 "is now a good time to sell cattle", "ano ang lagay ng presyo ngayon mataas ba o mura",
 "is the current price fair", "tama ba ang presyo ngayon", "buyers or sellers advantage this month",
 "para kanino ang magandang presyo ngayon buyer o seller", "rate the price for july",
 "ano ang rating ng presyo ngayong hunyo", "is the price this month considered high",
 "mababa ba ang presyo ngayong linggo", "how is the price level now"],
"price_trend": [
 "umaakyat ba ang presyo ng baka nitong mga nakaraang buwan", "has the price been rising lately",
 "ano ang galaw ng presyo", "how has the price moved since march", "pababa ba ang takbo ng presyo",
 "is the price trending up", "trend ng presyo mula enero hanggang hunyo",
 "price trend from january to june", "tuloy-tuloy ba ang pagtaas ng presyo",
 "is the cattle price falling lately", "ano ang pagbabago ng presyo sa nakaraang 3 buwan",
 "how did prices behave this year", "pabago-bago ba ang presyo",
 "are prices going up or down these months", "kilo trend this year"],
"price_compare": [
 "alin ang mas mahal enero o pebrero", "was april cheaper than march",
 "mas mataas ba ang kilo noong mayo kaysa abril", "compare march and june",
 "ihambing ang marso at hunyo", "which month had higher prices may or june",
 "mas mura ba ang hulyo kaysa hunyo", "difference between january and march prices",
 "pagkakaiba ng presyo ng enero at pebrero", "price in april against price in may",
 "mas marami ba ang baka noong marso kaysa pebrero", "compare the head count of june and july",
 "higher price august or september", "ihambing ang bilang ng baka ng abril at mayo",
 "mas mataas ba ang presyo ngayong buwan kumpara noong marso"],
"out_of_scope": [
 "uulan ba bukas", "will it rain today", "mainit ba ngayon", "ano ang lagay ng panahon",
 "is there a typhoon coming", "what is the news today", "ano ang balita ngayon",
 "who is the richest man", "sino ang pinakamayaman", "how do I make a resume",
 "paano gumawa ng resume", "what is the best phone", "anong cellphone ang maganda",
 "where can I eat nearby", "saan masarap kumain", "how to learn python",
 "paano matuto ng programming", "what is the exchange rate of the dollar",
 "magkano ang dolyar ngayon", "price of gasoline", "presyo ng gasolina", "magkano ang pamasahe",
 "how far is manila", "gaano kalayo ang maynila", "what is love", "ano ang pag-ibig",
 "can you be my friend", "pwede ba tayong maging magkaibigan", "what is the date today",
 "anong petsa ngayon", "play some music", "magpatugtog ka ng kanta", "what is two plus two",
 "tell me a story", "magkwento ka", "what is the price of gold", "presyo ng ginto",
 "price of eggs", "magkano ang itlog", "how do I treat a sick cow", "paano gamutin ang may sakit na baka"],
}

path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "intents.json")
with open(path, encoding="utf-8") as f:
    data = json.load(f)

added = 0
for intent, sentences in EXTRA.items():
    existing = data["intents"][intent]
    for s in sentences:
        if s not in existing:
            existing.append(s)
            added += 1

data["note"] = "DRAFT sentences written for development (2 rounds). Group should review and add more."
with open(path, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Added", added, "new sentences")
for k, v in data["intents"].items():
    print(f"  {k}: {len(v)}")
print("Total sentences:", sum(len(v) for v in data["intents"].values()))
