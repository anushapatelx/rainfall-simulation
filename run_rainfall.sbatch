#!/bin/bash
# The name of the job:
#SBATCH --job-name="rainfall_simulation"

# Send yourself an email when the job fails or ends:
#SBATCH --mail-type=FAIL
#SBATCH --mail-type=END
#SBATCH --mail-user=anushapx@umich.edu

# Resources: one node, one task, one CPU
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1

# Memory and time (adjust after the test run)
#SBATCH --mem=2g
#SBATCH --time=0-0:10:00

# Account and partition
#SBATCH --account="compfor203f26s001_class"
#SBATCH -p standard

# Separate stdout and stderr files (logs/ must exist BEFORE sbatch)
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err

# The modules to load:
module load mamba/py3.12

# The job command(s):
cd "$SLURM_SUBMIT_DIR"
mkdir -p results
eval "$(conda shell.bash hook)"
conda activate ~/envs/rainsim
export MPLBACKEND=Agg
export OMP_NUM_THREADS=1
echo "Hostname: $(hostname)"
echo "Date: $(date)"
echo "Python executable: $(python -c 'import sys; print(sys.executable)')"
echo "Python version: $(python --version)"
echo "$SLURM_JOB_ID" > results/job_id.txt
python run_simulation.py --years 3000000 --outdir results
python plot_results.py results
