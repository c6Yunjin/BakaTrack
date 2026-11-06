"""Writes data/router_examples.json: example questions per intent (drafted by the AI session)."""
import json

E = {}


def add(key, intent, need, block, title_en, title_fil, examples, title_taglish=None):
    E[key] = {"intent": intent, "need": need, "block": block,
              "title": {"en": title_en, "fil": title_fil, "taglish": title_taglish or title_fil},
              "examples": examples}


add("latest_price", "latest_price", [["latest"], ["price"]], "data",
    "What is the latest price of cattle in this dataset?", "Ano ang pinakabagong presyo ng baka sa dataset na ito?", [
        "what is the latest price of baka", "what is the most recent price of cattle per kilo",
        "current price of cows in the market", "newest price per kilo of cattle",
        "how much is baka right now", "what is the price of cattle today", "latest baka price",
        "ano ang pinakabagong presyo ng baka", "magkano ang baka ngayon",
        "ano ang kasalukuyang presyo ng baka sa palengke", "pinakabagong presyo ng baka kada kilo",
        "anong presyo ng baka ngayon"])
add("total_value", "total_value", [["value"], ["baka", "data", "market"]], "data",
    "What is the total value of the cattle sold?", "Ano ang kabuuang halaga ng mga baka na nabenta?", [
        "what is the total value of all cattle sold", "how much money was made from cattle sales",
        "total sales of baka this month", "how much did the cows sell for in total",
        "total revenue from cattle", "overall worth of the cattle traded", "total sales of the market",
        "ano ang kabuuang halaga ng baka na nabenta", "magkano ang kabuuang benta ng baka",
        "kabuuang halaga ng baka sa palengke", "total value ng baka ngayong buwan"])
add("price_per_head", "price_per_head", [["head", "each"], ["price", "average", "value"]], "data",
    "What is the average price per head?", "Ano ang average na presyo kada ulo?", [
        "average price per head", "how much does one head of cattle cost",
        "what is the price of each cow on average", "price per cow",
        "magkano ang average bawat ulo", "magkano ang isang baka sa average",
        "average na presyo kada ulo", "presyo ng bawat baka"])
add("weight_per_head", "weight_per_head", [["weight"], ["baka", "head", "each"]], "data",
    "What is the average weight per head?", "Ano ang average na bigat kada ulo?", [
        "how much does an average cow weigh", "average weight per head",
        "how heavy is the average cattle", "what is the weight of one baka",
        "gaano kabigat ang karaniwang baka", "ano ang karaniwang bigat ng baka",
        "gaano kabigat ang isang baka", "average na timbang kada ulo"])
add("market_summary", "market_summary", [["summary"], ["baka", "market", "data"]], "data",
    "Give me a summary of the cattle market", "Magbigay ng buod ng palengke ng baka", [
        "give me a summary of the cattle market", "quick overview of the cattle market",
        "market summary", "summary of the cattle data", "buod ng palengke ng baka",
        "buod ng datos ng baka"])
add("location_info", "location_info", [["data"], ["place", "source"]], "loc",
    "Where is this dataset from?", "Saan galing ang dataset na ito?", [
        "where did this dataset come from", "which place is this data from",
        "which place does this data cover", "what location is this dataset from",
        "which town is this data from", "where was this data collected",
        "saan galing itong datos na ito", "anong lugar ang saklaw ng datos na ito",
        "saang bayan galing ang datos", "saan nanggaling ang dataset"])
add("dataset_info", "dataset_info", [["data"], ["date", "many", "cover", "month"]], "data",
    "What dates and how many records does this dataset have?", "Anong mga petsa at ilang talaan ang meron sa dataset na ito?", [
        "what is the date range of the data", "how many records are in the dataset",
        "what are the first and last dates in the data", "which months does the data cover",
        "ilang records ang nasa dataset", "ano ang saklaw na petsa ng datos",
        "gaano karaming datos ang meron ka", "hanggang kailan ang datos"])
add("sys_about", "sys_about", [["you", "bot"]], "sys",
    "What can you do?", "Ano ang kaya mong gawin?", [
        "what can you do", "what are you", "tell me about yourself", "what is bakatrack",
        "what is this chatbot for", "what are you able to do", "what do you do",
        "ano ang magagawa mo", "ano ka", "ano ang bakatrack", "para saan ang chatbot na ito",
        "ano ang mga kaya mong gawin"])
add("sys_how", "sys_how", [["how"], ["work", "you", "bot"]], "sys_how",
    "How do you work?", "Paano ka gumagana?", [
        "how do you work", "how does this chatbot work", "how does bakatrack work",
        "explain how you work", "how do you understand my questions", "how do you find the answer",
        "paano ka gumagana", "paano gumagana ang chatbot na ito", "paano mo naiintindihan ang tanong ko",
        "ipaliwanag kung paano ka gumagana"])
add("sys_accuracy", "sys_accuracy", [["accuracy"]], "sys_acc",
    "How accurate are you?", "Gaano ka katumpak?", [
        "what is your accuracy", "how accurate are you", "how accurate is the chatbot",
        "what is the accuracy of the model", "how reliable are your answers", "how often are you correct",
        "ano ang accuracy mo", "gaano ka katumpak", "gaano katumpak ang mga sagot mo", "gaano ka maaasahan"])
add("sys_ai", "sys_ai", [["ai"]], "sys",
    "Are you using ChatGPT or any online AI?", "Gumagamit ka ba ng ChatGPT o online AI?", [
        "are you chatgpt", "are you using chatgpt", "do you use openai", "are you powered by gemini",
        "are you using an external ai", "do you use a pre trained model", "is this chatbot using an api",
        "how were you trained", "are you an ai", "gumagamit ka ba ng chatgpt", "ginagamit mo ba ang openai",
        "saan ka sinanay"])
add("sys_languages", "sys_languages", [["language"]], "sys",
    "What languages do you understand?", "Anong mga wika ang naiintindihan mo?", [
        "what languages do you understand", "do you speak filipino", "can i ask in tagalog",
        "do you understand taglish", "what languages do you support", "can you speak english",
        "anong wika ang naiintindihan mo", "marunong ka ba mag tagalog", "pwede ba akong magtanong sa tagalog",
        "ano ang mga wikang sinusuportahan mo"])
add("sys_forecast_how", "sys_forecast_how", [["forecast"], ["how", "accuracy", "method", "work"]], "",
    "How does the forecast work?", "Paano gumagana ang forecast?", [
        "how does the forecast work", "how do you make the forecast", "how is the forecast computed",
        "how accurate is the forecast", "what method does the forecast use",
        "paano ginagawa ang forecast", "paano gumagana ang hula", "gaano katumpak ang forecast"])
add("sys_rating_how", "sys_rating_how", [["rating"], ["how", "work", "method", "rating"]], "",
    "How does the price rating work?", "Paano gumagana ang price rating?", [
        "how does the price rating work", "how do you rate prices", "what is the fuzzy rating",
        "how does the fuzzy logic work", "what is fuzzy logic", "paano gumagana ang rating ng presyo",
        "ano ang fuzzy rating", "paano mo nirarate ang presyo"])
add("sys_limits", "sys_limits", [["limit"]], "",
    "What are your limitations?", "Ano ang mga limitasyon mo?", [
        "what are your limitations", "what can you not do", "what are you not able to do",
        "can i trust your answers", "can i rely on your answers", "should i trust the forecast",
        "ano ang mga limitasyon mo", "pwede ba akong magtiwala sa sagot mo", "ano ang hindi mo kaya"])

with open("data/router_examples.json", "w", encoding="utf-8") as f:
    json.dump(E, f, indent=2, ensure_ascii=False)
print("wrote", sum(len(v["examples"]) for v in E.values()), "example questions for", len(E), "intents")
