#!/usr/bin/env python3
"""
Tower of Hanoi - ASCII Terminal Edition
=========================================
A classic Tower of Hanoi game rendered with ASCII art in the terminal.

Rules:
  - Move all disks from peg A to peg C (or your chosen destination).
  - Only one disk may be moved at a time.
  - A larger disk may never be placed on top of a smaller disk.

Features:
  - ASCII-rendered pegs and disks, redrawn after every move.
  - Move counter + comparison against the theoretical minimum (2^n - 1).
  - Warns you if you pick a very large number of disks (rendering/legibility
    and exponential move count issues) and lets you back out.
  - Undo last move.
  - Auto-solve / hint mode that plays out the optimal solution move-by-move.
  - Input validation with helpful error messages instead of crashing.
  - Win screen with your move count vs optimal.
"""

import sys
import time

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

MIN_DISKS = 3
MAX_DISKS_SOFT_WARNING = 10   # above this, warn about huge move counts
MAX_DISKS_HARD_WARNING = 15   # above this, warn strongly about terminal width
PEG_NAMES = ["A", "B", "C"]


# ---------------------------------------------------------------------------
# Game state
# ---------------------------------------------------------------------------

class Hanoi:
    def __init__(self, num_disks):
        self.num_disks = num_disks
        # pegs[0] = A, pegs[1] = B, pegs[2] = C. Disk sizes: bigger number = bigger disk.
        self.pegs = [list(range(num_disks, 0, -1)), [], []]
        self.moves = 0
        self.history = []  # list of (from_idx, to_idx) for undo

    def peg_index(self, letter):
        letter = letter.strip().upper()
        if letter not in PEG_NAMES:
            return None
        return PEG_NAMES.index(letter)

    def can_move(self, src, dst):
        if src == dst:
            return False, "Source and destination pegs are the same."
        if not self.pegs[src]:
            return False, f"Peg {PEG_NAMES[src]} is empty — no disk to move."
        if self.pegs[dst] and self.pegs[dst][-1] < self.pegs[src][-1]:
            return False, (
                f"Can't place disk {self.pegs[src][-1]} on top of smaller "
                f"disk {self.pegs[dst][-1]} on peg {PEG_NAMES[dst]}."
            )
        return True, ""

    def move(self, src, dst, record=True):
        ok, reason = self.can_move(src, dst)
        if not ok:
            return False, reason
        disk = self.pegs[src].pop()
        self.pegs[dst].append(disk)
        self.moves += 1
        if record:
            self.history.append((src, dst))
        return True, ""

    def undo(self):
        if not self.history:
            return False, "Nothing to undo."
        src, dst = self.history.pop()
        # reverse the move without re-recording history, and don't count it
        # as a "real" move that helps the player win faster
        disk = self.pegs[dst].pop()
        self.pegs[src].append(disk)
        self.moves += 1  # undoing still costs a move, like real life
        return True, f"Undid move: {PEG_NAMES[src]} -> {PEG_NAMES[dst]}"

    def is_solved(self, target_peg=2):
        return len(self.pegs[target_peg]) == self.num_disks

    def optimal_moves(self):
        return 2 ** self.num_disks - 1


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

def render(game):
    n = game.num_disks
    peg_height = n + 1
    width = 2 * n + 1  # width of the widest disk

    lines = []
    for level in range(peg_height - 1, -1, -1):
        row = ""
        for p in range(3):
            stack = game.pegs[p]
            if level < len(stack):
                disk = stack[level]
                disk_width = 2 * disk + 1
                pad = (width - disk_width) // 2
                symbol = str(disk) if disk < 10 else chr(ord('a') + disk - 10)
                segment = " " * pad + symbol * disk_width + " " * pad
            else:
                pad = width // 2
                segment = " " * pad + "|" + " " * pad
            row += segment + "   "
        lines.append(row.rstrip())

    base = ""
    for p in range(3):
        base += "=" * width + "   "
    lines.append(base.rstrip())

    labels = ""
    for p in range(3):
        pad = width // 2
        labels += " " * pad + PEG_NAMES[p] + " " * pad + "   "
    lines.append(labels.rstrip())

    print("\n".join(lines))


def print_header(game):
    print("\n" + "=" * 50)
    print(f" TOWER OF HANOI   |  Disks: {game.num_disks}  |  Moves: {game.moves}"
          f"  |  Optimal: {game.optimal_moves()}")
    print("=" * 50)


# ---------------------------------------------------------------------------
# Setup / input helpers
# ---------------------------------------------------------------------------

def ask_num_disks():
    while True:
        raw = input(
            f"How many disks would you like to play with? "
            f"({MIN_DISKS}-{MAX_DISKS_SOFT_WARNING} recommended): "
        ).strip()
        if not raw.isdigit():
            print("Please enter a whole number.")
            continue
        n = int(raw)
        if n < MIN_DISKS:
            print(f"Minimum is {MIN_DISKS} disks for a meaningful game.")
            continue

        if n > MAX_DISKS_HARD_WARNING:
            print(
                f"\n⚠️  WARNING: {n} disks requires {2**n - 1:,} moves to solve "
                f"optimally, and the ASCII board will likely be wider than "
                f"your terminal, breaking the display."
            )
            confirm = input("Type 'yes' to proceed anyway, or press Enter to pick a smaller number: ").strip().lower()
            if confirm == "yes":
                return n
            else:
                continue

        elif n > MAX_DISKS_SOFT_WARNING:
            print(
                f"\n⚠️  Note: {n} disks means {2**n - 1:,} moves are needed to "
                f"solve optimally — that could take a while to play by hand."
            )
            confirm = input("Continue with this many? [y/N]: ").strip().lower()
            if confirm == "y":
                return n
            else:
                continue

        return n


def print_help():
    print("""
Commands:
  <from> <to>   Move a disk, e.g. "A C" moves the top disk from peg A to C
  undo          Undo your last move
  hint          Show the next optimal move (does not make it for you)
  auto          Watch the puzzle solve itself from the current position
  help          Show this help message
  quit          Exit the game
""")


# ---------------------------------------------------------------------------
# Solver (used for hints / auto-solve)
# ---------------------------------------------------------------------------

def solve_hanoi(n, src, aux, dst, moves_out):
    if n == 0:
        return
    solve_hanoi(n - 1, src, dst, aux, moves_out)
    moves_out.append((src, dst))
    solve_hanoi(n - 1, aux, src, dst, moves_out)


def remaining_solution(game):
    """
    Recompute an optimal path to completion from the CURRENT state.
    Simple approach: if the player has been playing 'legally' along the
    classic recursive pattern this lines up; if they've gone off-script we
    just recompute a fresh optimal solve for the sub-problem of getting
    everything onto peg C, disk by disk, largest first, using standard
    Hanoi recursion seeded with current peg locations.
    """
    # Simplest robust approach: solve from a fresh 3-peg formal state using
    # disk positions we have now would require full re-planning (Frame-Stewart
    # style state search). For a friendly hint feature, we instead just solve
    # the *entire* puzzle from scratch and show the player how many optimal
    # moves remain relative to their move count. If they've deviated, we solve
    # the remaining stack directly via BFS on the small state space.
    return bfs_next_move(game)


def bfs_next_move(game):
    """BFS over the (small) Hanoi state space to find the optimal next move
    from the current configuration to the solved state (all on peg C)."""
    from collections import deque

    start = tuple(tuple(p) for p in game.pegs)
    goal_count = game.num_disks

    def is_goal(state):
        return len(state[2]) == goal_count

    def neighbors(state):
        state = [list(p) for p in state]
        for i in range(3):
            for j in range(3):
                if i == j or not state[i]:
                    continue
                if state[j] and state[j][-1] < state[i][-1]:
                    continue
                new_state = [list(p) for p in state]
                disk = new_state[i].pop()
                new_state[j].append(disk)
                yield (i, j), tuple(tuple(p) for p in new_state)

    if is_goal(start):
        return None

    visited = {start}
    queue = deque([(start, [])])
    # Guard: cap BFS work for sanity (state space is 3^n, fine for n<=15ish
    # but this hint feature is really meant for reasonable disk counts)
    steps = 0
    max_steps = 200000
    while queue and steps < max_steps:
        steps += 1
        state, path = queue.popleft()
        for move, new_state in neighbors(state):
            if new_state in visited:
                continue
            new_path = path + [move]
            if is_goal(new_state):
                return new_path[0]
            visited.add(new_state)
            queue.append((new_state, new_path))
    return None


# ---------------------------------------------------------------------------
# Main game loop
# ---------------------------------------------------------------------------

def main():
    print("=" * 50)
    print("        TOWER OF HANOI — ASCII EDITION")
    print("=" * 50)
    print("Goal: move the entire stack from peg A to peg C.")
    print("Only smaller disks may sit on larger disks.\n")

    n = ask_num_disks()
    game = Hanoi(n)

    print_help()

    while True:
        print_header(game)
        render(game)

        if game.is_solved():
            print(f"\n🎉 Solved in {game.moves} moves! "
                  f"(Optimal was {game.optimal_moves()} moves)")
            if game.moves == game.optimal_moves():
                print("Perfect game — that's the minimum possible!")
            break

        try:
            raw = input("\nYour move ('help' for commands): ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            sys.exit(0)

        if not raw:
            continue

        cmd = raw.lower()

        if cmd in ("quit", "exit", "q"):
            print("Thanks for playing!")
            break

        elif cmd == "help":
            print_help()
            continue

        elif cmd == "undo":
            ok, msg = game.undo()
            print(msg)
            continue

        elif cmd == "hint":
            nxt = bfs_next_move(game)
            if nxt is None:
                print("No hint available (already solved or no path found).")
            else:
                src, dst = nxt
                print(f"Hint: move a disk from {PEG_NAMES[src]} to {PEG_NAMES[dst]}.")
            continue

        elif cmd == "auto":
            print("Auto-solving from current position...\n")
            while not game.is_solved():
                nxt = bfs_next_move(game)
                if nxt is None:
                    print("Could not find a solving path from here.")
                    break
                game.move(*nxt)
                render(game)
                print(f"Moved {PEG_NAMES[nxt[0]]} -> {PEG_NAMES[nxt[1]]}  "
                      f"(Moves: {game.moves})\n")
                time.sleep(0.4)
            continue

        parts = raw.split()
        if len(parts) != 2:
            print("Please enter two peg letters, e.g. 'A C'. Type 'help' for commands.")
            continue

        src = game.peg_index(parts[0])
        dst = game.peg_index(parts[1])
        if src is None or dst is None:
            print(f"Peg names must be one of {', '.join(PEG_NAMES)}.")
            continue

        ok, reason = game.move(src, dst)
        if not ok:
            print(f"Illegal move: {reason}")


if __name__ == "__main__":
    main()