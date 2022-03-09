import io

import discord.ext.commands

import settings


def place_emote(place: int):
    if place == 1:
        return ':first_place:'
    elif place == 2:
        return ':second_place:'
    elif place == 3:
        return ':third_place:'
    else:
        try:
            return settings.emotes[place]
        except KeyError:
            return f'`{place}`: '


def get_direction_arrow(rank, previous_rank, reverse=False):
    rank_delta = previous_rank - rank
    if reverse:
        if rank_delta > 0:
            direction = '↖️'
        elif rank_delta < 0:
            direction = '↙️'
        else:
            direction = '⬅️'
    else:
        if rank_delta > 0:
            direction = '↗️'
        elif rank_delta < 0:
            direction = '↘️'
        else:
            direction = '➡️'
    return direction


def plot2embed(ax) -> discord.File:  # funktion written by strange#3140, developer of the
    # league utils discord bot
    """generate an embed containing an image of the provided plot
    Parameters
    ----------
        ax: matplotlib.axes.Axes
            the plot
    Returns
    -------
        discord.File
            the attachment to send with the message
    """

    with io.BytesIO() as img_bytes:
        fig = ax.get_figure()
        fig.savefig(img_bytes, format='png')#, transparent=True)
        img_bytes.seek(0)
        image_file = discord.File(img_bytes, 'filename.png')
    return image_file
