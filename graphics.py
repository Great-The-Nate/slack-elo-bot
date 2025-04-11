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
