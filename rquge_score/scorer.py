from transformers import AutoModelForSequenceClassification, AutoTokenizer, T5Tokenizer, T5ForConditionalGeneration
from typing import Dict, List, Set
import re
import string


class RQUGE(object):
    def __init__(self, sp_scorer_path=None, device='cpu'):
        self.device = device

        ## initialize the span scorer module
        if sp_scorer_path is None:
            raise ValueError("Please Specify Span Scorer Model")
        self.sp_scorer = AutoModelForSequenceClassification.from_pretrained(sp_scorer_path).to(self.device)
        self.sp_scorer.eval()
        self.tokenizer_sp = AutoTokenizer.from_pretrained(sp_scorer_path)

    def normalize_answer(self, s):
        """Lower text and remove punctuation, articles and extra whitespace.
        """

        def remove_articles(text):
            return re.sub(r'\b(a|an|the)\b', ' ', text)

        def white_space_fix(text):
            return ' '.join(text.split())

        def remove_punc(text):
            exclude = set(string.punctuation)
            return ''.join(ch for ch in text if ch not in exclude)

        def lower(text):
            return text.lower()

        return white_space_fix(remove_articles(remove_punc(lower(s))))

    def predict_sp_score(self, input_sp):
        inputs = self.tokenizer_sp(input_sp, max_length=512, truncation=True, \
                                   padding="max_length", return_tensors="pt")
        outputs = self.sp_scorer(input_ids=inputs["input_ids"].to(self.device), \
                                 attention_mask=inputs["attention_mask"].to(self.device))
        outputs = [x[0] for x in outputs[0].cpu().tolist()]
        # outputs = [{"pred_score": x} for x in outputs]

        return outputs[0]

    def scorer(self, context, pred_question, pred_answer, gold_answer, max_new_tokens=30):
        ## compute the score for the predicted answer span

        input_sp = f"{self.normalize_answer(pred_question)} <q> {self.normalize_answer(gold_answer)} <r>" \
                   f" {self.normalize_answer(pred_answer)} <c> {self.normalize_answer(context)}"
        score = self.predict_sp_score(input_sp)

        return score
