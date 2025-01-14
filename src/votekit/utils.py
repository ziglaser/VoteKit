from collections import namedtuple
from fractions import Fraction
import random
from typing import Union, Iterable, Optional

from .ballot import Ballot
from .pref_profile import PreferenceProfile


COLOR_LIST = [
    (0.55, 0.71, 0.0),
    (0.82, 0.1, 0.26),
    (0.44, 0.5, 0.56),
    (1.0, 0.75, 0.0),
    (1.0, 0.77, 0.05),
    (0.0, 0.42, 0.24),
    (0.13, 0.55, 0.13),
    (0.9, 0.13, 0.13),
    (0.08, 0.38, 0.74),
    (0.41, 0.21, 0.61),
    (1.0, 0.72, 0.77),
    (1.0, 0.66, 0.07),
    (1.0, 0.88, 0.21),
    (0.55, 0.82, 0.77),
]

# Election Helper Functions
CandidateVotes = namedtuple("CandidateVotes", ["cand", "votes"])


def compute_votes(candidates: list, ballots: list[Ballot]) -> list[CandidateVotes]:
    """
    Computes first place votes for all candidates in a preference profile

    Args:
        candidates: List of all candidates in a PreferenceProfile
        ballots: List of Ballot objects

    Returns:
        List of tuples (candidate, number of votes) ordered by first place votes
    """
    votes = {cand: Fraction(0) for cand in candidates}

    for ballot in ballots:
        if not ballot.ranking:
            continue
        first_place_cand = unset(ballot.ranking[0])
        if isinstance(first_place_cand, list):
            for cand in first_place_cand:
                votes[cand] += ballot.weight / len(first_place_cand)
        else:
            votes[first_place_cand] += ballot.weight

    ordered = [
        CandidateVotes(cand=key, votes=value)
        for key, value in sorted(votes.items(), key=lambda x: x[1], reverse=True)
    ]

    return ordered


def fractional_transfer(
    winner: str, ballots: list[Ballot], votes: dict, threshold: int
) -> list[Ballot]:
    """
    Calculates fractional transfer from winner, then removes winner
    from the list of ballots

    Args:
        winner: Candidate to transfer votes from
        ballots: List of Ballot objects
        votes: Contains candidates and their corresponding vote totals
        threshold: Value required to be elected, used to calculate transfer value

    Returns:
        Modified ballots with transfered weights and the winning canidated removed
    """
    transfer_value = (votes[winner] - threshold) / votes[winner]

    for ballot in ballots:
        new_ranking = []
        if ballot.ranking and ballot.ranking[0] == {winner}:
            ballot.weight = ballot.weight * transfer_value
            for cand in ballot.ranking:
                if cand != {winner}:
                    new_ranking.append(cand)

    return remove_cand(winner, ballots)


def random_transfer(
    winner: str, ballots: list[Ballot], votes: dict, threshold: int
) -> list[Ballot]:
    """
    Cambridge-style transfer where transfer ballots are selected randomly

    Args:
        winner: Candidate to transfer votes from
        ballots: List of Ballot objects
        votes: Contains candidates and their corresponding vote totals
        threshold: Value required to be elected, used to calculate transfer value

    Returns:
        Modified ballots with transfered weights and the winning canidated removed
    """

    # turn all of winner's ballots into (multiple) ballots of weight 1
    weight_1_ballots = []
    for ballot in ballots:
        if ballot.ranking and ballot.ranking[0] == {winner}:
            # note: under random transfer, weights should always be integers
            for _ in range(int(ballot.weight)):
                weight_1_ballots.append(
                    Ballot(
                        id=ballot.id,
                        ranking=ballot.ranking,
                        weight=Fraction(1),
                        voters=ballot.voters,
                    )
                )

    # remove winner's ballots
    ballots = [
        ballot
        for ballot in ballots
        if not (ballot.ranking and ballot.ranking[0] == {winner})
    ]

    surplus_ballots = random.sample(weight_1_ballots, int(votes[winner]) - threshold)
    ballots += surplus_ballots

    transfered = remove_cand(winner, ballots)

    return transfered


def seqRCV_transfer(
    winner: str, ballots: list[Ballot], votes: dict, threshold: int
) -> list[Ballot]:
    """
    Transfer method Sequential RCV elections

    Args:
        winner: Candidate to transfer votes from
        ballots: List of Ballot objects
        votes: Contains candidates and their corresponding vote totals
        threshold: Value required to be elected, used to calculate transfer value

    Returns:
        Original list of ballots as Sequential RCV does not transfer votes
    """
    return ballots


def remove_cand(removed: Union[str, Iterable], ballots: list[Ballot]) -> list[Ballot]:
    """
    Removes specified candidate(s) from ballots

    Args:
        removed: Candidate or set of candidates to be removed
        ballots: List of Ballots to remove canidate(s) from

    Returns:
        Updated list of ballots with candidate(s) removed
    """
    if isinstance(removed, str):
        remove_set = {removed}
    elif isinstance(removed, Iterable):
        remove_set = set(removed)

    update = []
    for ballot in ballots:
        new_ranking = []
        if len(remove_set) == 1 and remove_set in ballot.ranking:
            for s in ballot.ranking:
                new_s = s.difference(remove_set)
                if new_s:
                    new_ranking.append(new_s)
            update.append(
                Ballot(
                    id=ballot.id,
                    ranking=new_ranking,
                    weight=ballot.weight,
                    voters=ballot.voters,
                )
            )
        elif len(remove_set) > 1:
            for s in ballot.ranking:
                new_s = s.difference(remove_set)
                if new_s:
                    new_ranking.append(new_s)
            update.append(
                Ballot(
                    id=ballot.id,
                    ranking=new_ranking,
                    weight=ballot.weight,
                    voters=ballot.voters,
                )
            )
        else:
            update.append(ballot)

    return update


def order_candidates_by_borda(candidate_set: set, candidate_borda: dict) -> list:
    """
    Sorts candidates based on their Borda values

    Args:
        candidate_set: Candidates to be sorted
        candidate_borda: Dictionary of candidates and their Borda values

    Returns:
        Ordered set of candidates for based on Borda values
    """
    # Sort the candidates in candidate_set based on their Borda values
    ordered_candidates = sorted(
        candidate_set, key=lambda candidate: (-candidate_borda[candidate], candidate)
    )
    return ordered_candidates


# Summmary Stat functions
def first_place_votes(profile: PreferenceProfile) -> dict:
    """
    Calculates first-place votes for a PreferenceProfile

    Args:
        profile: Inputed profile of ballots

    Returns:
        Dictionary of candidates (keys) and first place vote totals (values)
    """
    cands = profile.get_candidates()
    ballots = profile.get_ballots()

    return {cand: float(votes) for cand, votes in compute_votes(cands, ballots)}


def mentions(profile: PreferenceProfile) -> dict:
    """
    Calculates total mentions for a PreferenceProfile

    Args:
        profile: Inputed profile of ballots

    Returns:
        Dictionary of candidates (keys) and mention totals (values)
    """
    mentions: dict[str, float] = {}

    ballots = profile.get_ballots()
    for ballot in ballots:
        for rank in ballot.ranking:
            for cand in rank:
                if cand not in mentions:
                    mentions[cand] = 0
                if len(rank) > 1:
                    mentions[cand] += (1 / len(rank)) * int(
                        ballot.weight
                    )  # split mentions for candidates that are tied
                else:
                    mentions[cand] += float(ballot.weight)

    return mentions


def borda_scores(
    profile: PreferenceProfile,
    ballot_length: Optional[int] = None,
    score_vector: Optional[list] = None,
) -> dict:
    """
    Calculates Borda scores for a PreferenceProfile

    Args:
        profile: Inputed profile of ballots
        ballot_length: Length of a ballot, if None length of longest ballot is \n
        is used
        score_vector: Borda weights, if None assigned based length of longest \n
        ballot


    Returns:
        Dictionary of candidates (keys) and Borda scores (values)
    """
    candidates = profile.get_candidates()
    if ballot_length is None:
        ballot_length = max([len(ballot.ranking) for ballot in profile.ballots])
    if score_vector is None:
        score_vector = list(range(ballot_length, 0, -1))

    candidate_borda = {c: Fraction(0) for c in candidates}
    for ballot in profile.ballots:
        current_ind = 0
        candidates_covered = []
        for s in ballot.ranking:
            position_size = len(s)
            local_score_vector = score_vector[current_ind : current_ind + position_size]
            borda_allocation = sum(local_score_vector) / position_size
            for c in s:
                candidate_borda[c] += Fraction(borda_allocation) * ballot.weight
            current_ind += position_size
            candidates_covered += list(s)

        # If ballot was incomplete, evenly allocation remaining points
        if current_ind < len(score_vector):
            remainder_cands = set(candidates).difference(set(candidates_covered))
            remainder_score_vector = score_vector[current_ind:]
            remainder_borda_allocation = sum(remainder_score_vector) / len(
                remainder_cands
            )
            for c in remainder_cands:
                candidate_borda[c] += (
                    Fraction(remainder_borda_allocation) * ballot.weight
                )

    return candidate_borda


def unset(input: set):
    """
    Removes object from set

    Args:
        input: Input set

    Returns:
        If set has length one returns the object, else returns a list
    """
    rv = list(input)

    if len(rv) == 1:
        return rv[0]

    return rv
