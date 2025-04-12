import textwrap
import matplotlib.pyplot as plt


def matrix_to_ascii_table(matrix):
    if not matrix or not all(isinstance(row, list) for row in matrix):
        return "Invalid matrix input"

    # Determine number of columns
    num_cols = max(len(row) for row in matrix)

    # Normalize matrix rows to have the same number of columns
    for row in matrix:
        row += [''] * (num_cols - len(row))

    # Calculate the max width for each column
    col_widths = [max(len(str(row[i])) for row in matrix) for i in range(num_cols)]

    def wrap_row(row):
        """Wraps each cell in the row to its column width"""
        wrapped_cells = [textwrap.wrap(str(cell), width=col_widths[i]) or [''] for i, cell in enumerate(row)]
        max_lines = max(len(lines) for lines in wrapped_cells)
        wrapped_rows = []
        for line_idx in range(max_lines):
            line_cells = []
            for i in range(num_cols):
                line = wrapped_cells[i][line_idx] if line_idx < len(wrapped_cells[i]) else ''
                line_cells.append(f' {line.ljust(col_widths[i])} ')
            wrapped_rows.append('|' + '|'.join(line_cells) + '|')
        return wrapped_rows

    # Border line
    border = '+' + '+'.join('-' * (w + 2) for w in col_widths) + '+'

    # Assemble table
    lines = [border]
    for row in matrix:
        row_lines = wrap_row(row)
        for line in row_lines:
            lines.append(line)
        lines.append(border)

    return '\n'.join(lines)


def generate_bracket_image(players_matrix, filename):
    '''
    Accepts a matrix of teams to write into the bracket where
    players_matrix[r][p] is the pth (player, score) in round r.
    If players_matrix[r] is given, all matches in the round must be given with at least a None value

    Ex: 
    teams = [
        [("A", 5), ("B", 5), ("C", 5), ("D", 5), ("E", 0), ("F", 0), (None, None), (None, None)], 
        [("A", 5), ("C", 1), ("E", 100), ("G", 600)], 
        [("A", None), ("G", None)], 
        [("A", None)]
    ]
    '''

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.axis("off")

    num_players = len(players_matrix[0])
    rounds = num_players.bit_length()
    spacing_x = 1.0
    spacing_y = 1.0
    text_padding_y = 0.03 * (2 ** (rounds-2))


    # joint_ys[r][m] = the y coord of the mth match in the rth round
    joint_ys = []
    for r in range(rounds):
        players_in_round = num_players // (2**r)
        joint_ys.append([])
        for p in range(players_in_round):
            # joint_ys[r].append((joint_ys[r-1][2*p] + joint_ys[r-1][2*p+1]) / 2)
            joint_ys[r].append((2**(r-1) - 1) * spacing_y + p * 2**r * spacing_y + spacing_y/2)

            x = spacing_x * r
            y = joint_ys[r][p]

            if r == 0 and players_matrix[r][p][0] == None:
                # If it's a first round bye, don't draw anything
                continue
            
            # For a given player, draw its horizontal line and a vertical connector to the next round (unless it's the last round)
            ax.plot([x, x+spacing_x], [y, y], "k-")
            if r != rounds-1:
                vertical_line_direction = 1 if p % 2 == 0 else -1
                ax.plot([x + spacing_x, x + spacing_x], [y, y + vertical_line_direction * spacing_y/2 * 2**r], "k-")

            if len(players_matrix) > r:
                player, score = players_matrix[r][p]
                ax.text(x + 0.05, y + text_padding_y, player if player else "", ha="left", va="center", fontsize=10)
                ax.text(x + spacing_x - 0.05, y + text_padding_y, str(score) if score else "", ha="right", va="center", fontsize=10)

    plt.savefig(filename, bbox_inches='tight')
