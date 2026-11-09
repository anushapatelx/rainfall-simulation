{\rtf1\ansi\ansicpg1252\cocoartf2822
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fswiss\fcharset0 Helvetica;}
{\colortbl;\red255\green255\blue255;}
{\*\expandedcolortbl;;}
\margl1440\margr1440\vieww10820\viewh13040\viewkind0
\pard\tx720\tx1440\tx2160\tx2880\tx3600\tx4320\tx5040\tx5760\tx6480\tx7200\tx7920\tx8640\pardirnatural\partightenfactor0

\f0\fs24 \cf0 This program models rainfall over a certain number of years to investigate the difference between two places that have the same average rainfall, but one place has steady rainfall whilst the other place has rainfall that comes in clusters (seasonal rainfall).\
\
rainism.py:\
Modules: numpy, pandas \
uses the probability that a dry day will become a wet day the next day (p_dry_wet) and the probability that a wet day will still be wet day the next day (p_wet_wet). p_wet_wet addresses the condition that rainfall comes in clusters. It also sets the average rainfall to being the same across both conditions. For the p_dry_wet condition, it uses a cosine wave to model seasonal peaks of rainfall. The function simulate years will loops through every day of the year and returns a pandas table with one row per year and the average rainfall on each day of they year. The function summarize will  summarize the pandas table into mean annual rain, standard deviation of that mean, the drought years, and the mean longest dry spell. The function run_scanrios then runs the simulation for each p_wet_wet value.\
\
run_simulation.py:\
Modules: argparse, os, time\
Creates summary.csv, annual_sample.cvs and daily_profile.csv\
\
plot_results.py:\
Module: os, lib, matplotlib\
Uses the three csv\'92s created from run_simulation.py and makes a histogram with this information \
\
test_rainism.py:\
Runs test cases uses pytest on edge cases\
\
Environment:\
name: rainsim\
channels:\
  - conda-forge\
dependencies:\
  - python=3.12\
  - numpy\
  - pandas\
  - matplotlib\
  - pytest\
\
Interpretation of results:\
According to the csv tables and summary.png, as the probability of seasonal rain (p_wet_wet increases) there is a higher probability of there being a drought year and a longer mean dry spell. There is also a higher average rain (mm/day) in the middle of the year (may). This simulation suggests that with a higher probability of seasonal rain (with the probability that a wet day will preceed a wet day), there is a higher risk of dry spells and drought years.\
\
\
}