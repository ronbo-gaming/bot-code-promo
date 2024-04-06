import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix='&', intents=intents)

# Dictionary to store active codes with their expiration time and unit
active_codes = {}

YOUR_ROLE_ID = None  # Replace with the ID of the role allowed to use the addcode command
YOUR_CHANNEL_ID = None  # Replace with the ID of the channel to send the added code
EXPIRED_CHANNEL_ID = None  # Replace with the ID of the channel to send expired code messages
TOKEN = "YOUR_DISCORD_BOT_TOKEN"  # Replace with your bot token

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

@bot.command(name="addcode",
             description="Add a discount code with an expiration time")
@commands.has_role(YOUR_ROLE_ID)
async def add_code(ctx: commands.Context, code: str, reduction_percentage: str, expiration_time: str):
    if not code or not reduction_percentage or not expiration_time:
        embed = discord.Embed(title="Ronbo Code Promo", description="Please provide all parameters: code, reduction percentage, and expiration time.", color=discord.Color.red())
        await ctx.send(embed=embed)
        return
    
    try:
        reduction_percentage = float(reduction_percentage.strip('%'))
        if reduction_percentage < 1 or reduction_percentage > 100:
            raise ValueError
    except ValueError:
        embed = discord.Embed(title="Ronbo Code Promo", description="Invalid reduction percentage. Please provide a valid percentage between 1% and 100%.", color=discord.Color.red())
        await ctx.send(embed=embed)
        return
    
    # Extract expiration time and unit
    expiration_time = expiration_time.lower()
    units = {'h': 'hours', 'm': 'minutes', 's': 'seconds'}
    unit = expiration_time[-1]
    if unit not in units:
        embed = discord.Embed(title="Ronbo Code Promo", description="Invalid expiration time unit. Please use 'h' (hours), 'm' (minutes), or 's' (seconds).", color=discord.Color.red())
        await ctx.send(embed=embed)
        return
    
    try:
        expiration_value = int(expiration_time[:-1])
        if expiration_value <= 0:
            raise ValueError
    except ValueError:
        embed = discord.Embed(title="Ronbo Code Promo", description="Invalid expiration time value. Please provide a valid positive integer.", color=discord.Color.red())
        await ctx.send(embed=embed)
        return

    expiration = datetime.utcnow() + timedelta(**{units[unit]: expiration_value})
    active_codes[code] = (expiration, reduction_percentage, expiration_time)
    
    # Get the channel where you want to send the code
    channel = bot.get_channel(YOUR_CHANNEL_ID)
    if channel:
        embed = discord.Embed(title="Ronbo Code Promo", description=f"Discount code '{code}' added successfully with {reduction_percentage}% reduction, expiring in {expiration_time}.", color=discord.Color.green())
        embed.set_footer(text=f"Expires at: {expiration}")
        await channel.send(embed=embed)
    
    embed = discord.Embed(title="Ronbo Code Promo", description=f"Discount code '{code}' added successfully with {reduction_percentage}% reduction, expiring in {expiration_time}.", color=discord.Color.green())
    await ctx.send(embed=embed)

@add_code.error
async def add_code_error(ctx, error):
    if isinstance(error, commands.MissingRole):
        embed = discord.Embed(title="Ronbo Code Promo", description="You do not have the required role to use this command.", color=discord.Color.red())
        await ctx.send(embed=embed)

@tasks.loop(seconds=1)
async def check_expired_codes():
    now = datetime.utcnow()
    expired_codes = [(code, (expiration, reduction, expiration_time)) for code, (expiration, reduction, expiration_time) in active_codes.items() if expiration < now]
    for code, (expiration, reduction, expiration_time) in expired_codes:
        del active_codes[code]
        channel = bot.get_channel(EXPIRED_CHANNEL_ID)
        if channel:
            embed = discord.Embed(title="Ronbo Code Promo", description=f"The discount code '{code}' has expired after {expiration_time}.", color=discord.Color.red())
            await channel.send(embed=embed)

check_expired_codes.start()

@bot.command(name="bot_help",
             description="Show available commands")
async def bot_help(ctx: commands.Context):
    help_message = """
    Available Commands:
    &addcode <code> <reduction_percentage> <expiration_time> - Add a discount code. Example: &addcode RONBO2024 20% 1h
    &checkcode <code> - Check if a discount code is expired or still active
    &calculate <amount> <reduction_percentage> - Calculate discounted amount. Example: &calculate 1000 35
    """
    embed = discord.Embed(title="Ronbo Code Promo", description=help_message, color=discord.Color.blue())
    await ctx.send(embed=embed)

@bot.command(name="checkcode",
             description="Check if a discount code is expired or working")
async def check_code(ctx: commands.Context, code: str):
    if code in active_codes:
        expiration, _, expiration_time = active_codes[code]
        if expiration > datetime.utcnow():
            await ctx.send(f"The discount code '{code}' is still active.")
        else:
            await ctx.send(f"The discount code '{code}' has expired after {expiration_time}.")
    else:
        await ctx.send(f"The discount code '{code}' does not exist.")

@bot.command(name="calculate",
             description="Calculate discounted amount")
async def calculate(ctx: commands.Context, amount: float, reduction_percentage: float):
    if reduction_percentage < 1 or reduction_percentage > 100:
        embed = discord.Embed(title="Ronbo Code Promo", description="Invalid reduction percentage. Please provide a valid percentage between 1% and 100%.", color=discord.Color.red())
        await ctx.send(embed=embed)
        return

    discounted_amount = amount - (amount * reduction_percentage / 100)
    embed = discord.Embed(title="Ronbo Code Promo", description=f"After applying a {reduction_percentage}% discount, the amount is {discounted_amount}.", color=discord.Color.green())
    await ctx.send(embed=embed)

bot.run(TOKEN)
