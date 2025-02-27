python main.py --no_solar_gain \
            --agent_type=ppo \
            --agents_comm_mode=neighbours \
            --alpha_sig=1 \
            --alpha_temp=1 \
            --batch_size=256 \
            --env_seed=1 \
            --exp=PPO \
            --gamma=0.99 \
            --lr_both=0.01 \
            --max_grad_norm=1 \
            --nb_agents=50 \
            --nb_agents_comm=0 \
            --nb_inter_saving_actor=24 \
            --net_seed=2 \
            --save_actor_name=PPO \
            --temp_penalty_mode=individual_L2 \
            --time_step=4 \
            --no_wandb