from __future__ import print_function

def dep_searcher(sents,
                 search,
                 show=['w'],
                 dep_type='collapsed-ccprocessed-dependencies',
                 regex_nonword_filter=r'[A-Za-z0-9:_]',
                 do_concordancing=False,
                 exclude=False,
                 excludemode='any',
                 searchmode='all',
                 lemmatise=False,
                 case_sensitive=False,
                 only_format_match=False,
                 speaker=False,
                 gramsize=2,
                 nopunct=True,
                 split_contractions=False,
                 window=2):
    """
    search corenlp dependency parse
    1. search for 'search' keyword arg
       governor
       dependent
       function
       pos
       lemma
       word
       index
       etc

    2. exclude entries if need be, using same method as search

    3. return results and conc lines, or just a count
       """
    import re
    from corenlp_xml.document import Document
    from collections import Counter
    from corpkit.build import flatten_treestring
    from corpkit.process import filtermaker, animator, get_deps

    is_a_word = re.compile(regex_nonword_filter)

    if any(x.startswith('n') for x in show) \
    or any(x.startswith('b') for x in show):
        only_format_match = True

    ####################################################
    ################ SEARCH FUNCTIONS ##################
    ####################################################

    def search_word(deprole, pattern):
        matches = set()
        if deprole == 'm':
            for tok in tokens:
                if re.search(pattern, tok.word):
                    matches.add(tok)
        elif deprole == 'd':
            for link in deps.links:
                if re.search(pattern, link.dependent.text):
                    matches.add(s.get_token_by_id(link.governor.idx))
        elif deprole == 'g':
            for link in deps.links:
                if re.search(pattern, link.governor.text):
                    matches.add(s.get_token_by_id(link.dependent.idx))
        return matches

    mapshorts = {'d': 'dependents',
                 'g': 'governors'}

    def search_lemma(deprole, pattern):
        matches = set()
        for tok in tokens:
            if not re.search(pattern, tok.lemma):
                continue
            if deprole == 'm':
                matches.add(tok)
                continue
            else:
                node = deps.get_node_by_idx(tok.id)
                for subn in getattr(node, mapshorts[deprole]):
                    matches.add(s.get_token_by_id(subn.idx))
        return matches

    def search_pos(deprole, pattern):
        matches = set()
        for tok in tokens:
            if not re.search(pattern, tok.pos):
                continue
            if deprole == 'm':
                matches.add(tok)
                continue
            else:
                node = deps.get_node_by_idx(tok.id)
                for subn in getattr(node, mapshorts[deprole]):
                    matches.add(s.get_token_by_id(subn.idx))
        return matches

    def search_wordclass(deprole, pattern):
        from corpkit.dictionaries.word_transforms import taglemma
        matches = set()
        for tok in tokens:
            postag = tok.pos
            wordclass = taglemma.get(postag.lower(), postag.lower())
            if not re.search(pattern, tok.pos):
                continue
            if deprole == 'm':
                matches.add(tok)
                continue
            else:
                node = deps.get_node_by_idx(tok.id)
                for subn in getattr(node, mapshorts[deprole]):
                    matches.add(s.get_token_by_id(subn.idx))
        return matches

    def search_function(deprole, pattern):
        matches = set()
        if deprole == 'g':
           for l in deps.links:
                if not re.search(pat, l.type):
                    continue
                gov_index = l.dependent.idx
                for l2 in deps.links:
                    if not l2.governor.idx == gov_index:
                        continue
                    matches.add(s.get_token_by_id(l2.dependent.idx))
        else:
            for link in deps.links:
                if not re.search(pat, link.type):
                    continue
                if deprole == 'd':
                    matches.add(s.get_token_by_id(link.governor.idx))
                if deprole == 'm':
                    matches.add(s.get_token_by_id(link.dependent.idx))
        return matches

    def search_distance(deprole, pattern):
        matches = set()
        for tok in tokens:
            if deprole == 'm':
                tosearch = [tok]
            else:
                node = deps.get_node_by_idx(tok.id)
                tosearch = []
                for subn in getattr(node, mapshorts[deprole]):
                    tosearch.append(s.get_token_by_id(subn.idx))
            for t in tosearch:
                dist = distancer(deps.links, tk)
                if dist is None or dist is False:
                    continue
                try:
                    if int(dist) == int(pat):
                        matches.add(tok)
                except TypeError:
                    if re.search(pat, str(dist)):
                        matches.add(tok)
        return matches

    def search_index(deprole, pattern):
        matches = set()
        for tok in tokens:
            if not re.search(pattern, str(tok.id)):
                continue
            if deprole == 'm':
                matches.add(tok)
                continue
            else:
                node = deps.get_node_by_idx(tok.id)
                for subn in getattr(node, mapshorts[deprole]):
                    matches.add(s.get_token_by_id(subn.idx))
        return matches


    lookup_search = {'w': search_word,
                     'l': search_lemma,
                     'r': search_distance,
                     'i': search_index,
                     'p': search_pos,
                     'f': search_function,
                     'x': search_wordclass}

    ####################################################
    ################## SHOW FUNCTIONS ##################
    ####################################################

    # if show functions are terminal, they return the word
    # if they aren't, they return token instances

    def show_word(token_set):
        return [tok.word for tok in token_set]

    def show_lemma(token_set):
        from corpkit.dictionaries.word_transforms import wordlist
        return [wordlist.get(tok.lemma, tok.lemma) \
                for tok in token_set]

    def show_pos(token_set):
        return [tok.pos for tok in token_set]

    def show_wordclass(token_set):
        from corpkit.dictionaries.word_transforms import taglemma
        return [taglemma.get(tok.pos.lower(), tok.pos) \
                for tok in token_set]

    def show_function(token_set):
        fs = []
        for tok in token_set:
            for i in deps.links:
                if i.dependent.idx == tok.id:
                    fs.append(i.type.rstrip(','))
        return fs


    def show_distance(token_set):
        fs = set()
        for tok in token_set:
            all_matching_token_s = [l for l in deps.links]
            distance = distancer(all_matching_tokens, tok)
            if distance is not False and distance is not None:
                fs.add(str(distance))
        return fs

    def show_index(token_set):
        return set([str(tok.id) for tok in token_set])

    def show_governor(token_set):
        govs = set()
        for tok in token_set:
            for i in deps.links:
                if i.dependent.idx == tok.id:
                    gov = s.get_token_by_id(i.governor.idx)
                    if gov:
                        govs.add(gov)
        return govs

    def show_dependent(token_set):
        dat = set()
        for tok in token_set:
            for i in deps.links:
                if i.governor.idx == tok.id:
                    dep = s.get_token_by_id(i.dependent.idx)
                    if dep:
                        dat.add(dep)
        return dat

    def show_next(token_set):
        """get token to the right"""
        nexts = set()
        for tok in token_set:
            current_index = tokens.index(tok)
            try:
                nexts.add(tokens[current_index + 1])
            except IndexError:
                pass
        return nexts

    lookup_show = {'w': show_word,
                   'l': show_lemma,
                   'g': show_governor,
                   'd': show_dependent,
                   'r': show_distance,
                   'i': show_index,
                   'p': show_pos,
                   'f': show_function,
                   'x': show_wordclass,
                   'o': show_next
                   }

    ####################################################
    ################ PROCESSING FUNCS ##################
    ####################################################

    def get_list_of_lookup_funcs(show):
        """take a single search/show type, return match"""
        #show = [i.lstrip('n').lstrip('b') for i in show]
        ends = ['w', 'l', 'i', 'n', 'f', 'p', 'x']
        show = list(show)
        if show[-1] not in ends:
            show.append('w')
        return [lookup_show[i] for i in show]

    def get_search_func(srch):
        return lookup_search[srch[-1]]

    def fix_search(search):
        """if search has nested dicts, remove them"""
        ends = ['w', 'l', 'i', 'n', 'f', 'p', 'x']
        if not search:
            return
        newsearch = {}
        for srch, pat in search.items():
            if len(srch) == 1 and srch in ends:
                srch = 'm' + srch
            if isinstance(pat, dict):
                for k, v in list(pat.items()):
                    if k != 'w':
                        newsearch[srch + k] = pat_format(v)
                    else:
                        newsearch[srch] = pat_format(v)
            else:
                newsearch[srch] = pat_format(pat)
        return newsearch

    def do_single_search(srch, pat):
        """get results from single search criterion"""
        matching_tokens = set()
        func = get_search_func(srch)
        matches = func(srch[0], pat)
        for i in matches:
            matching_tokens.add(i)
        return matching_tokens

    def distancer(matching_tokens, token):
        "determine number of jumps to root"      
        c = 0
        # get the gov index, stop when it's zero
        root_found = False
        while not root_found:
            if c == 0:
                try:
                    link_to_check = next(i for i in matching_tokens if i.dependent.idx == token.id)
                except StopIteration:
                    root_found = True
                    break
                #link_to_check = token
            gov_index = link_to_check.governor.idx
            if gov_index == 0:
                root_found = True
            else:
                if c > 29:
                    root_found = True
                    break
                link_to_check = [l for l in matching_tokens if l.dependent.idx == gov_index]
                if len(link_to_check) > 0:
                    link_to_check = link_to_check[0]
                else:
                    break
                c += 1
        if c < 30:
            return c

    def pat_format(pat):
        from corpkit.dictionaries.process_types import Wordlist
        if isinstance(pat, Wordlist):
            pat = list(pat)
        if pat == 'any':
            pat = re.compile(r'.*')
        elif isinstance(pat, list):
            if all(isinstance(x, int) for x in pat):
                pat = [str(x) for x in pat]
            pat = filtermaker(pat, case_sensitive=case_sensitive)
        else:
            if case_sensitive:
                pat = re.compile(pat)
            else:
                pat = re.compile(pat, re.IGNORECASE)
        return pat

    def process_a_match(match, tokens):
        """
        Take a single search match and return a list of results and conc lines
        """
        resultlist = []
        conclist = []
        for repeat in range(repeats):
            res, conc_res = process_a_submatch(match, repeat, tokens)
            if not res and not conc_res:
                continue
            #for r, c in zip(res, conc_res):
            resultlist.append(res)
            conclist.append(conc_res)
        return resultlist, conclist

    def get_indices(match, repeat, tokens):
        """
        Get first and last index in token list for a token
        """
        
        py_index = tokens.index(match)        
        # first time around, start at the word
        # second time, at the word - 1

        # if ngramming, we need an index of the last token in the ngram
        if any(x.startswith('n') for x in show):

            first_in_gram = py_index - repeat
            last_in_gram = first_in_gram + (gramsize - 1)
        
        elif any(x.startswith('b') for x in show):
            first_in_gram = py_index - window + repeat
            last_in_gram = py_index - window + repeat
            if first_in_gram == py_index:
                return False, False
        else:
            py_index = tokens.index(match)
            first_in_gram = py_index - repeat
            last_in_gram = first_in_gram
        return first_in_gram, last_in_gram

    def process_a_submatch(match, repeat, tokens):
        """
        For ngrams, etc., we have to repeat over results. so, thisis for 
        each repeat
        """

        # make a conc line with just speaker name so far
        speakr = s.speakername
        if not speakr:
            speakr = ''
        # begin building line with speaker first
        conc_line = [speakr]

        # get the index of the match in python
        first_in_gram, last_in_gram = get_indices(match, repeat, tokens)
        if first_in_gram is False and last_in_gram is False:
            return False, False

        # maybe we can't repeat over it, because it's at the start or end
        # in this case, return
        if first_in_gram < 0:
            return False, False
        if last_in_gram >= len(tokens):
            return False, False

        # by this point, we have the index of the start and end of the gram
        # now, if we don't need the whole sent, we discard it. if we don't
        # need to format it, we format it now.

        if do_concordancing:
            if only_format_match or show == ['n'] or show == ['b']:
                start = ' '.join(t.word for index, t in enumerate(tokens) \
                    if index < first_in_gram)
                end = ' '.join(t.word for index, t in enumerate(tokens) \
                    if index > last_in_gram)
                # and only process the match itself
                # redefine tokens to just be what we need        
                tokens = tokens[first_in_gram:last_in_gram+1]
                # add back the original token to left/right of collocate
                if any(x.startswith('b') for x in show):
                    if repeat == 0:
                        tokens.append(match)
                    elif repeats / repeat > 0:
                        tokens.append(match)
                    else:
                        tokens.insert(0, match)

        # if we are concordancing, here's a list of toks in the ngram
        else:
            tokens = tokens[first_in_gram:last_in_gram+1]

        if any(x.startswith('b') for x in show):
            separator = '_'
        else:
            separator = ' '

        # now, for each word in the matching sentence, format it.
        # note that if we're not doing concordancing, or if only formatting 
        # the match (or not concordancing), len(tokens) == 1
        processed_toklist = []
        for token in tokens:
            single_result = process_a_token(token, show)
            for bit in single_result:
                processed_toklist.append(bit)
        
        # if no conc at all, return the empty ish one and a string of token(s)
        if not do_concordancing:
            return ' '.join(processed_toklist), conc_line

        # if we're concordancing:
        # now we have formatted tokens as a list. we need to split
        # it into start, middle and end, unless only_format_match
        else:
            if not only_format_match:
                start = ' '.join(w for index, w in enumerate(processed_toklist) \
                                 if index < first_in_gram)
                end = ' '.join(w for index, w in enumerate(processed_toklist) \
                                 if index > last_in_gram)
                middle = separator.join(w for index, w in enumerate(processed_toklist) \
                                 if index >= first_in_gram \
                    and index <= last_in_gram)
            else:
                middle = separator.join(processed_toklist)

            for bit in start, middle, end:
                conc_line.append(bit)

        return middle, conc_line

    def process_a_token(token, show):
        """
        Take entire show argument, and a token of interest,
        and return slash sep token
        """
        # make an iterable token, because this can generate more than one token
        # if searching for dependent, for example
        intermediate_result = []
        # for each show value, add the correct representation to the list
        for val in show:
            tok = {token}
            funcs = get_list_of_lookup_funcs(val)
            for func in funcs:
                tok = func(tok)
            for t in tok:
                intermediate_result.append(t)
        return ['/'.join(intermediate_result)]

    ####################################################
    ################## BEGIN WORKFLOW ##################
    ####################################################

    # if we're doing ngrams or collocations, we need to repeat over the data
    # otherwise it's just once
    repeats = 1
    if any(x.startswith('n') for x in show):
        repeats = gramsize
    if any(x.startswith('b') for x in show):
        repeats = (window * 2) + 1

    # store results here
    result = []
    conc_result = []

    # fix search and excludes
    search = fix_search(search)
    exclude = fix_search(exclude)

    # iterate over sentences
    for s in sents:

        # all search matches go here
        matching_tokens = []
        deps = get_deps(s, dep_type)
        # remove punctuation if need be
        if nopunct:
            tokens = [w for w in s.tokens if re.search(is_a_word, w.word)]
        else:
            tokens = s.tokens
        # identify matching Token objects
        #matching_tokens = get_matches_from_sent(s, search, deps, tokens, 
        #                                        dep_type, mode=searchmode)
        for srch, pat in search.items():
            matches = do_single_search(srch, pat)
            matching_tokens += matches

        # exclude in the same way if need be
        removes =[]
        if exclude:
            for excl, expat, in exclude:
                for remove in do_single_search(excl, expat):
                    removes.append(remove)
                
            # do removals
            for i in removes:
                try:
                    matching_tokens.remove(i)
                except ValueError:
                    pass

        # if counting, we're done already
        if 'c' in show:
            result.append(len(matching_tokens))
            continue

        # iterate over results, entering processing loops
        for match in matching_tokens:
            # they are returned as lists, so add those to final result
            res, conc_res = process_a_match(match, tokens)
            for r, c in zip(res, conc_res):
                if r and c:
                    result.append(r)
                    conc_result.append(c)

    if 'c' in show:
        result = sum(result)

    if isinstance(do_concordancing, basestring) and do_concordancing.lower() == 'only':
        result = []

    if not do_concordancing:
        conc_result = []

    return result, conc_result