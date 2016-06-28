import re

'''
    Track Title Componenet Classifications

     T -> AR DL FTN ME | AR DL FT | FT
    AR -> AR L AN | AN L AN | AN
    AN -> Proper Noun
     L -> List Delimiter
    DL -> Title Delimiter
    FT -> Noun Phrase
    ME -> MO MT MC | ME ME
    MO -> Meta Opening Delimiter
    MT -> Noun Phrase
    MC -> Meta Closing Delimiter
    
    T = Track Title
    AR = Artist Phrase
    AN = Artist Name
    L = List Delimiter (commas, other punc., 'and', 'including', etc.)
    DL = Title Delimiter (by far most likely '-')
    FT = Title Phrase
    ME = Meta Clause, ex. often times a track ends in (Explicit) or (Year) or (HQ)
    MO = Meta Clause Opening Character, probably '(' or '['
    MC = Meta Clause Closing Character, probably ')' or ']'

'''

TITLE_REGEX = r'^([\w\s]+)(\s?[\-]\s?)([\w\s]+)((\s?\([^)(]+\)\s?)*)$'
_T_REGEX = re.compile(TITLE_REGEX)

'''
    For each token in the title, if we have seen that token before:
        check the frequency that token has appeared in both successful and rejected
        candidates in the past, and then compare those numbers

        if the token is often seen in rejected tracks, as in the THRESHOLD < #reject/#total < 1.0
            fail_likely = true

        if the token is often seen in accepted tracks,
            accept_likely = true

        if fail_likely and not accept_likely:
            suggest reject
        elif not fail_likely and accept_likely:
            suggest accept
        elif fail_likely and accept_likely:
            suggest unsure
        else:
            suggest irrelevant

'''


def FilterResults(results):
    approved = []
    rejected = []
    for r in results:
        title = r['candidate']['title']
        match = _T_REGEX.match(title)
        if match is None:
            rejected.append(r)
            continue
        
        # Could do information extraction here using capture groups, then do further NLP
        # on the results to further improve accuracy
        approved.append(r)

    return (approved, rejected)

