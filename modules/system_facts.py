"""System facts (hand-written). Answers questions about the chatbot itself.

The accuracy numbers below come from training/evidence/results.json. If you retrain, update them here.
"""
HIDDEN, CV, SD = "84.76%", "84.71%", "3.23%"

INTENTS = {"sys_about", "sys_how", "sys_accuracy", "sys_ai", "sys_languages",
           "sys_forecast_how", "sys_rating_how", "sys_limits"}

TEXT = {}
TEXT["sys_about"] = {
    "en": "I am BakaTrack PH, a chatbot for cattle market records. Pick a dataset and ask about kilos, head count, prices, the highest or lowest month, comparisons, trends, charts, forecasts and price ratings, or ask me to show the records. You can write in English, Filipino or Taglish. I also know a few facts about Padre Garcia, with sources.",
    "fil": "Ako si BakaTrack PH, isang chatbot para sa talaan ng palengke ng baka. Pumili ng dataset at magtanong tungkol sa kilo, bilang ng ulo, presyo, pinakamataas o pinakamababang buwan, paghahambing, takbo ng presyo, tsart, pagtataya at antas ng presyo, o hilingin na ipakita ang mga talaan. Maaari kang sumulat sa English, Filipino o Taglish. May alam din ako tungkol sa Padre Garcia, kasama ang pinagmulan.",
    "taglish": "Ako si BakaTrack PH, isang chatbot para sa cattle market records. Pumili ng dataset at magtanong tungkol sa kilos, head count, presyo, highest o lowest na buwan, comparison, trend, chart, forecast at price rating, o hilingin na ipakita ang records. Pwede kang mag-type sa English, Filipino o Taglish. May alam din ako tungkol sa Padre Garcia, with sources.",
}
TEXT["sys_how"] = {
    "en": "Your message is cleaned first. Hand-written rules and a similarity matcher check for known question types. If none fits, a neural network (ANN) that we trained ourselves on our own example sentences picks the intent. If it is less than 60% sure, I show a referral message instead of guessing. Then a rule-based parser reads the dates, a query engine computes the numbers from the selected dataset only, and written templates build the answer. No online AI service is used, and it works offline.",
    "fil": "Nililinis muna ang mensahe mo. Sinusuri ng mga hand-written na rules at ng similarity matcher ang mga kilalang uri ng tanong. Kung walang tumugma, isang neural network (ANN) na sinanay namin sa sarili naming mga halimbawang pangungusap ang pipili ng intent. Kung mas mababa sa 60% ang tiwala nito, magpapakita ako ng referral message sa halip na manghula. Pagkatapos, binabasa ng rule-based na parser ang mga petsa, kinukuwenta ng query engine ang mga numero mula sa napiling dataset lamang, at ang mga nakasulat na template ang bumubuo ng sagot. Walang ginagamit na online AI service at gumagana ito kahit offline.",
    "taglish": "Nililinis muna ang message mo. Chine-check ng hand-written rules at ng similarity matcher ang mga kilalang uri ng tanong. Kung walang tumugma, isang neural network (ANN) na sinanay namin sa sarili naming example sentences ang pipili ng intent. Kung mas mababa sa 60% ang confidence, referral message ang ipapakita ko, hindi manghuhula. Tapos binabasa ng rule-based parser ang dates, kinukuwenta ng query engine ang numbers mula sa napiling dataset lang, at templates ang bumubuo ng sagot. Walang online AI service na ginagamit, at gumagana ito offline.",
}
TEXT["sys_accuracy"] = {
    "en": "The intent classifier (ANN) scored {hidden} on a hidden test set (about 85%) and {cv} (± {sd}) in 5-fold cross-validation. The example sentences were written for this project in one style, so real users' wording may score lower. Below 60% confidence I do not guess.",
    "fil": "Ang intent classifier (ANN) ay nakakuha ng {hidden} sa hidden test set (halos 85%) at {cv} (± {sd}) sa 5-fold cross-validation. Ang mga halimbawang pangungusap ay isinulat para sa proyektong ito sa iisang istilo, kaya maaaring mas mababa ang resulta sa tunay na pananalita ng mga user. Kapag mas mababa sa 60% ang tiwala, hindi ako nanghuhula.",
    "taglish": "Ang intent classifier (ANN) ay nakakuha ng {hidden} sa hidden test set (halos 85%) at {cv} (± {sd}) sa 5-fold cross-validation. Ang example sentences ay isinulat para sa project na ito sa iisang style, kaya baka mas mababa ang score sa totoong wording ng users. Kapag mas mababa sa 60% ang confidence, hindi ako manghuhula.",
}
TEXT["sys_ai"] = {
    "en": "No. I do not use ChatGPT, Gemini, Claude or any other online AI service or pre-trained model. The intent classifier was trained on our own sentences, the fuzzy price rater and forecaster are hand-written, and everything runs offline.",
    "fil": "Hindi. Hindi ako gumagamit ng ChatGPT, Gemini, Claude o anumang online AI service o pre-trained na model. Ang intent classifier ay sinanay sa sarili naming mga pangungusap, ang fuzzy price rater at forecaster ay isinulat nang mano-mano, at lahat ay gumagana nang offline.",
    "taglish": "Hindi. Hindi ako gumagamit ng ChatGPT, Gemini, Claude o anumang online AI service o pre-trained model. Ang intent classifier ay sinanay sa sarili naming sentences, ang fuzzy price rater at forecaster ay hand-written, at lahat ay offline.",
}
TEXT["sys_languages"] = {
    "en": "I understand English, Filipino and Taglish. I reply in the same language as your question: Filipino gets Filipino, English gets English and Taglish gets Taglish. Slang and very short messages can be misread; if I am unsure, I will say so.",
    "fil": "Naiintindihan ko ang English, Filipino at Taglish. Sumasagot ako sa parehong wika ng tanong mo: Filipino kung Filipino, English kung English at Taglish kung Taglish. Maaaring magkamali sa slang o napakaikling mensahe; kung hindi ako sigurado, sasabihin ko.",
    "taglish": "Naiintindihan ko ang English, Filipino at Taglish. Sumasagot ako sa same language ng tanong mo: Filipino kung Filipino, English kung English at Taglish kung Taglish. Pwedeng magkamali sa slang o napakaikling message; kung hindi ako sure, sasabihin ko.",
}
TEXT["sys_forecast_how"] = {
    "en": "The forecast uses simple methods written by hand: the average of the last 3 months, or a straight trend line. It tests both on the last 3 known months and uses the one with the smaller error (MAPE and MAE). It needs at least 6 months of records, shows the months used, and is only an estimate, a guide and not a guarantee. It does not claim seasonal patterns.",
    "fil": "Gumagamit ang forecast ng simpleng paraan na isinulat nang mano-mano: ang average ng huling 3 buwan, o isang tuwid na linya ng takbo. Sinusubukan ang dalawa sa huling 3 kilalang buwan at ginagamit ang may mas maliit na error (MAPE at MAE). Kailangan nito ng hindi bababa sa 6 na buwan ng talaan, ipinapakita ang mga buwang ginamit, at pagtataya lamang ito, gabay at hindi garantiya. Walang inaangking pana-panahong pattern.",
    "taglish": "Gumagamit ang forecast ng simpleng methods na hand-written: ang average ng huling 3 buwan, o isang straight trend line. Tine-test ang dalawa sa huling 3 kilalang buwan at ginagamit ang may mas maliit na error (MAPE at MAE). Kailangan nito ng at least 6 na buwan ng records, ipinapakita ang months used, at estimate lang ito, gabay at hindi garantiya. Walang inaangking seasonal pattern.",
}
TEXT["sys_rating_how"] = {
    "en": "The price rating is a hand-written fuzzy system. It divides the month's average price by the dataset's overall average price to get a ratio, measures how much the ratio belongs to Low, Normal and High (membership shapes), fires the rules (Low: buyers have the advantage, High: sellers do), and takes the centroid to get a score from 0 to 100. It needs at least 3 months of records and is a guide only.",
    "fil": "Ang price rating ay hand-written na fuzzy system. Hinahati nito ang average na presyo ng buwan sa kabuuang average na presyo ng dataset para makuha ang ratio, sinusukat kung gaano ito kabilang sa Low, Normal at High, pinapaandar ang mga rule (Low: may kalamangan ang mamimili, High: may kalamangan ang nagbebenta), at kinukuha ang centroid para sa score na 0 hanggang 100. Kailangan nito ng hindi bababa sa 3 buwan ng talaan at gabay lamang ito.",
    "taglish": "Ang price rating ay hand-written na fuzzy system. Hinahati nito ang average price ng buwan sa overall average price ng dataset para makuha ang ratio, sinusukat kung gaano ito kabilang sa Low, Normal at High, pinapaandar ang rules (Low: advantage ng buyers, High: advantage ng sellers), at kinukuha ang centroid para sa score na 0 hanggang 100. Kailangan nito ng at least 3 buwan ng records at gabay lang ito.",
}
TEXT["sys_limits"] = {
    "en": "I only answer from the records in the selected dataset and a few verified Padre Garcia facts. I have no live prices or live auction inventory. Forecasts and ratings are estimates, not guarantees. Sample datasets contain fake demo data and are labeled SAMPLE. If I am unsure or there is no data, I say so and suggest the market office or the Municipal Agriculture Office.",
    "fil": "Sumasagot lamang ako mula sa mga talaan ng napiling dataset at ilang napatunayang katotohanan tungkol sa Padre Garcia. Wala akong live na presyo o live na imbentaryo ng auction. Ang forecast at rating ay pagtataya, hindi garantiya. Ang mga sample dataset ay may pekeng demo data at may label na SAMPLE. Kung hindi ako sigurado o walang datos, sasabihin ko at imumungkahi ang market office o ang Municipal Agriculture Office.",
    "taglish": "Sumasagot lang ako mula sa records ng napiling dataset at ilang verified facts tungkol sa Padre Garcia. Wala akong live prices o live auction inventory. Ang forecast at rating ay estimates, hindi garantiya. Ang sample datasets ay may fake demo data at may label na SAMPLE. Kung hindi ako sure o walang data, sasabihin ko at imumungkahi ang market office o ang Municipal Agriculture Office.",
}


def reply(intent, lang):
    texts = TEXT[intent]
    text = texts.get(lang) or texts["en"]
    return text.format(hidden=HIDDEN, cv=CV, sd=SD)
