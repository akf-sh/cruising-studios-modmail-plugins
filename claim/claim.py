import discord
from discord.ext import commands

from core import checks
from core.checks import PermissionLevel


class ClaimThread(commands.Cog):
    """Allows supporters to claim thread by sending claim in the thread channel"""
    def __init__(self, bot):
        self.bot = bot
        self.db = self.bot.plugin_db.get_partition(self)
        check_reply.fail_msg = 'This thread has been claimed by another user.'
        self.bot.get_command('reply').add_check(check_reply)
        self.bot.get_command('areply').add_check(check_reply)
        self.bot.get_command('fareply').add_check(check_reply)
        self.bot.get_command('freply').add_check(check_reply)

    @checks.has_permissions(PermissionLevel.SUPPORTER)
    @checks.thread_only()
    @commands.command()
    async def claim(self, ctx):
        thread = await self.db.find_one({'thread_id': str(ctx.thread.channel.id)})
        if thread is None:
            await self.db.insert_one({'thread_id': str(ctx.thread.channel.id), 'claimers': [str(ctx.author.id)]})
            await ctx.send(f'<@{str(ctx.author.id)}> you have successfully claimed this thread.')
        else:
            if len(thread['claimers']) == 0:
                await self.db.update_one({
                    'thread_id': str(ctx.thread.channel.id)
                }, {
                    '$set': {
                        'claimers': [str(ctx.author.id)]
                    }
                })
                await ctx.send(f'<@{str(ctx.author.id)}> you have successfully claimed this thread.')

            else:
                await ctx.send('Thread is already claimed')

    @checks.has_permissions(PermissionLevel.SUPPORTER)
    @checks.thread_only()
    @commands.command()
    async def unclaim(self, ctx):
        thread = await self.db.find_one({'thread_id': str(ctx.thread.channel.id)})
        if thread is None:
            await ctx.send(f'<@{str(ctx.author.id)}>, there is no claim on this thread.')
        else:
            if len(thread['claimers']) > 0 and str(ctx.author.id) in thread['claimers']:
                await self.db.update_one({
                    'thread_id': str(ctx.thread.channel.id)
                }, {
                    '$pull': {
                        'claimers': str(ctx.author.id)
                    }
                })
                await ctx.send(f'<@{str(ctx.author.id)}> you have successfully unclaimed this thread.')

            else:
                await ctx.send(f'<@{str(ctx.author.id)}>, you have no claim on this thread.')
                

    @checks.has_permissions(PermissionLevel.SUPPORTER)
    @checks.thread_only()
    @commands.command()
    async def addclaim(self, ctx, *, member: discord.Member):
        """Adds another user to the thread claimers"""
        thread = await self.db.find_one({'thread_id': str(ctx.thread.channel.id)})
        if thread and str(ctx.author.id) in thread['claimers']:
            await self.db.find_one_and_update({'thread_id': str(ctx.thread.channel.id)}, {'$addToSet': {'claimers': str(member.id)}})
            await ctx.send('Added to claimers')

    @checks.has_permissions(PermissionLevel.SUPPORTER)
    @checks.thread_only()
    @commands.command()
    async def removeclaim(self, ctx, *, member: discord.Member):
        """Removes a user from the thread claimers"""
        thread = await self.db.find_one({'thread_id': str(ctx.thread.channel.id)})
        if thread and str(ctx.author.id) in thread['claimers']:
            await self.db.find_one_and_update({'thread_id': str(ctx.thread.channel.id)}, {'$pull': {'claimers': str(member.id)}})
            await ctx.send('Removed from claimers')

    @checks.has_permissions(PermissionLevel.SUPPORTER)
    @checks.thread_only()
    @commands.command()
    async def transferclaim(self, ctx, *, member: discord.Member):
        """Removes all users from claimers and gives another member all control over thread"""
        thread = await self.db.find_one({'thread_id': str(ctx.thread.channel.id)})
        if thread and str(ctx.author.id) in thread['claimers']:
            await self.db.find_one_and_update({'thread_id': str(ctx.thread.channel.id)}, {'$set': {'claimers': [str(member.id)]}})
            await ctx.send('Added to claimers')

    @checks.has_permissions(PermissionLevel.MODERATOR)
    @checks.thread_only()
    @commands.command()
    async def overrideaddclaim(self, ctx, *, member: discord.Member):
        """Allow mods to bypass claim thread check in add"""
        thread = await self.db.find_one({'thread_id': str(ctx.thread.channel.id)})
        if thread:
            await self.db.find_one_and_update({'thread_id': str(ctx.thread.channel.id)}, {'$addToSet': {'claimers': str(member.id)}})
            await ctx.send('Added to claimers')

    @checks.has_permissions(PermissionLevel.MODERATOR)
    @checks.thread_only()
    @commands.command()
    async def overridereply(self, ctx, *, msg: str=""):
        """Allow mods to bypass claim thread check in reply"""
        await ctx.invoke(self.bot.get_command('reply'), msg=msg)
        
    @checks.has_permissions(PermissionLevel.SUPPORTER)
    @checks.thread_only()
    @commands.command()
    async def claims(self, ctx):
        """List all claims on the current thread"""
        thread = await self.db.find_one({'thread_id': str(ctx.thread.channel.id)})
        if thread:
            claimers = thread.get('claimers', [])
            if claimers:
                claimers_formatted = [f'<@{claimer}>' for claimer in claimers]
                claimers_list = "\n".join(claimers_formatted)
                await ctx.send(f'Current claims on this thread:\n{claimers_list}')
            else:
                await ctx.send(f'There are currently no claims on this thread.')
        else:
            await ctx.send(f'There are currently no claims on this thread.')




async def check_reply(ctx):
    thread = await ctx.bot.get_cog('ClaimThread').db.find_one({'thread_id': str(ctx.thread.channel.id)})
    if thread and len(thread['claimers']) > 0:
        return ctx.author.bot or str(ctx.author.id) in thread['claimers']
    return True


async def setup(bot):
    await bot.add_cog(ClaimThread(bot))