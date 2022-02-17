"""MIT License

Copyright (c) 2019-2021 PythonistaGuild

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import wavelink
from discord.ext import commands
import discord


class Bot(commands.Bot):

    def __init__(self):
        super().__init__(command_prefix='>?')

    async def on_ready(self):
        print('Bot is ready!')


class Music(commands.Cog):
    """Music cog to hold Wavelink related commands and listeners."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

        bot.loop.create_task(self.connect_nodes())

        self.players = {}
        self.channels = {}
        self.queues = {}

    async def connect_nodes(self):
        """Connect to our Lavalink nodes."""
        await self.bot.wait_until_ready()

        await wavelink.NodePool.create_node(bot=self.bot,
                                            host='0.0.0.0',
                                            port=2333,
                                            password='YOUR_LAVALINK_PASSWORD')

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, node: wavelink.Node):
        """Event fired when a node has finished connecting."""
        print(f'Node: <{node.identifier}> is ready!')

    @commands.Cog.listener()
    async def on_wavelink_track_end(self, player: wavelink.Player, track: wavelink.Track, reason):
        queue: wavelink.Queue = self.queues.get(player.guild.id)
        channel: discord.Channel = self.channels.get(player.guild.id)
        if not queue.is_empty:
            await player.play(queue.get())
            await channel.send("Now playing: " + str(player.track))

    @commands.command()
    async def join(self, ctx: commands.Context):
        """Joins a voice channel."""
        if not ctx.voice_client:
            vc: wavelink.Player = await ctx.author.voice.channel.connect(cls=wavelink.Player)
        else:
            vc: wavelink.Player = ctx.voice_client

        self.players[ctx.guild.id] = vc
        self.queues[ctx.guild.id] = wavelink.Queue()
        self.channels[ctx.guild.id] = ctx.channel

    @commands.command()
    async def play(self, ctx: commands.Context, *, search: wavelink.YouTubeTrack):
        """Play a song with the given search query.

        If something is already playing, add to the queue.
        """

        if ctx.guild.id not in self.players.keys():
            await ctx.invoke(self.join)

        vc: wavelink.Player = self.players.get(ctx.guild.id)
        queue: wavelink.Queue = self.queues.get(ctx.guild.id)

        if (not queue.is_empty) or vc.is_playing():
            queue.put(search)
            await ctx.send("Added to queue: " + str(search))
        else:
            await vc.play(search)
            await ctx.send("Now playing: " + str(search))


    @commands.command()
    async def skip(self, ctx: commands.Context):
        """Skips to the next song in the queue."""
        player: wavelink.Player = self.players.get(ctx.guild.id)
        if not player:
            return await ctx.send("Not connected to a voice channel")
        
        queue: wavelink.Queue = self.queues.get(player.guild.id)
        if not queue.is_empty:
            await player.play(queue.get())
            await ctx.send("Now playing: " + str(player.track))


    @commands.command()
    async def queue(self, ctx: commands.Context):
        """Displays the next 5 songs in the queue."""
        player: wavelink.Player = self.players.get(ctx.guild.id)
        if not player:
            return await ctx.send("Not connected to a voice channel")
        
        queue: wavelink.Queue = self.queues.get(player.guild.id)
        tracks = []
        for track in queue:
            tracks.append(str(track))

        tracks = tracks[:5]
        string = "Next 5 tracks:"
        for n, t in enumerate(tracks):
            string = string + "\n" + str(n + 1) + ": " + t
        
        await ctx.send(string)
    

bot = Bot()
bot.add_cog(Music(bot))
bot.run('YOUR_BOT_TOKEN')