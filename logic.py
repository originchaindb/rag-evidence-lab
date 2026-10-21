import re

def evaluate(data):
    docs = data['documents']
    if not isinstance(docs,dict) or not all(isinstance(k,str) and isinstance(v,str) for k,v in docs.items()):
        raise ValueError('documents must map IDs to text')
    cases = data['cases']
    if not isinstance(cases,list) or not cases:
        raise ValueError('cases must not be empty')
    results, seen = [], set()
    for case in cases:
        cid, answer = case['id'], case['answer']
        if not isinstance(cid,str) or not cid or cid in seen or not isinstance(answer,str):
            raise ValueError('invalid or duplicate case')
        seen.add(cid)
        if type(case['answerable']) is not bool or type(case['abstained']) is not bool:
            raise ValueError('answerable and abstained must be booleans')
        facts = case['expected_terms']
        if not isinstance(facts,list) or any(not isinstance(f,str) or not f.strip() for f in facts):
            raise ValueError('invalid expected terms')
        citations = case['citations']
        if not isinstance(citations,list):
            raise ValueError('citations must be a list')
        reasons = []
        if case['answerable']:
            if not facts:
                raise ValueError('answerable cases need expected terms')
            if case['abstained']:
                reasons.append('unexpected_abstention')
            for term in facts:
                if term.casefold() not in answer.casefold():
                    reasons.append('missing_expected_term:' + term)
            if not citations:
                reasons.append('missing_citation')
        elif not case['abstained']:
            reasons.append('should_abstain')
        for citation in citations:
            docid, quote = citation['document_id'], citation['quote']
            if docid not in docs:
                reasons.append('unknown_citation')
            elif not isinstance(quote,str) or not quote.strip() or quote not in docs[docid]:
                reasons.append('quote_not_in_document')
        results.append({'id':cid,'passed':not reasons,'reasons':reasons})
    return {'passed':all(r['passed'] for r in results),'cases':results,'pass_rate':sum(r['passed'] for r in results)/len(results),'grading':'literal checks, not semantic entailment'}
