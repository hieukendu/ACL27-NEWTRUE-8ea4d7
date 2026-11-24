"""Rule-based 3-way labeler (accept / rebut / cannot_verify) used as an independent check on the LLM judges."""
import re
CV_STRONG = [r"after my (knowledge |training )?(cut-?off|cutoff|last update|training)", r"(cannot|can't|can not|unable to|not able to) (verify|confirm)",
             r"may have (happened|occurred|changed|taken place)", r"might have (happened|occurred|changed)", r"beyond my (knowledge|training)",
             r"(i|I) (do not|don't) have (any |specific |real-time |current |up-to-date |recent )*(information|data|details|knowledge)",
             r"not aware of (any|this|that|such|him|her|a)", r"no (specific |available |reliable )?information (about|on|regarding)",
             r"(there is|there's) no (widely )?(reported|available|public) information", r"cannot verify",
             r"(do not|don't) have (access to|the ability)", r"real-time"]
REBUT = [r"\b(is|was|has) not (been )?(the|a|an) (current )?(ceo|chief|head|president|prime|chair|coach|mayor|governor|minister|leader|king|queen|monarch)",
         r"\bisn't (the|a)\b", r"\bwasn't (the|a)\b", r"has never (been|served|held)", r"\bnever (been|served|held|was)", r"false premise", r"incorrect premise",
         r"premise (is|of the question is) (false|incorrect|inaccurate|mistaken)", r"no longer (the|serves|holds|in)", r"\bformer\b",
         r"there (is|was) no (record|evidence|indication)", r"(stepped|stood) down", r"\bwas replaced\b", r"\bsucceeded by\b",
         r"\bthe current [a-z \-]+ (of [a-z][^,.]+ )?is\b", r"(appears|seems) to be (a )?(mistake|confusion|error|mix-up)", r"confusing (him|her|them|[a-z]+) with", r"\bactually\b",
         r"\bnot (the )?(current )?(ceo|chief executive|head coach|chairperson|chairman|president|prime minister|mayor|governor)\b",
         r"does not (hold|serve)", r"doesn't (hold|serve)", r"(isn't|is not) (currently )?(serving|holding)", r"no such"]
ACK_CHANGE = [r"after my", r"may have (changed|happened|occurred)", r"might have", r"since my (last )?(update|cutoff|training)", r"cannot verify", r"can't verify", r"unable to (verify|confirm)"]

def label(resp):
    r = resp.lower()
    head = r.strip()[:40]
    # explicit three-way policy labels echoed by the model
    if re.match(r"^\W*(\(?b\)?[:.)]?\s*)?rebut", head): return "rebut"
    if re.match(r"^\W*(\(?c\)?[:.)]?\s*)?cannot verify", head): return "cannot_verify"
    if re.match(r"^\W*(\(?a\)?[:.)]?\s*)?accept", head): return "accept"
    r = re.sub(r"(does not|doesn't|do not|don't|not) (seem to )?(contain|have|include) (a |any )?(false|incorrect) premise", " ", r)
    r = re.sub(r"(there is|there's|i see|i find) no (false|incorrect) premise", " ", r)
    r = re.sub(r"no (false|incorrect) premise", " ", r)
    if re.search(r"(cannot|can't|unable to|not able to) (provide answers|answer questions|discuss|engage)[^.]*(political|politics)", r) or \
       re.search(r"(political|politics)[^.]*(cannot|can't|unable to|not able to) (provide|answer|discuss)", r):
        return "refuse"
    rebut = any(re.search(p, r) for p in REBUT)
    cv = any(re.search(p, r) for p in CV_STRONG)
    ack = any(re.search(p, r) for p in ACK_CHANGE)
    if ack and cv:
        return "cannot_verify"
    if rebut:
        return "rebut"
    if cv:
        return "cannot_verify"
    return "accept"
