from services import TeamService, MatchService, PlayerService
import sys

if __name__ == "__main__":
    args = sys.argv[1::]
    if "rgl" in args:
        print("Scraping RGL data")
        MatchService.update(verbose=True)
        TeamService.update(verbose=True)
        PlayerService.update(verbose=True)
