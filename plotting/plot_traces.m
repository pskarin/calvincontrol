close all

experi_date = '20180117';
experi_names = {'mpc_baseline_rt_new_scheduler_plant','mpc_baseline_default_scheduler_plant', 'mpc_baseline_rt_default_scheduler_plant'};

node_map = {'Unknown', 'RP-1', 'RP-2', 'RP-3', 'RP-4', 'Edge-1', 'DC-1', 'AWS-EUC1'};

nbr_experis = length(experi_names);
nbr_analy = 5;

nbr_col = nbr_analy;
nbr_row = nbr_experis;

for i = 1:nbr_experis
    disp(experi_names{i})
    
    if length(strfind(lower(experi_names{i}),'pid')) > 0 
        type = 1;
        actor_methods = {'act_write'; 'inner_cal_output'; 'outer_cal_output'; 'ang_trigger'; 'dis_clocktick'; 'pos_trigger'; 'inner_cal_output_queue_minmax'; 'outer_cal_output_queue_minmax';'ang_trigger_queue_minmax'; 'dis_clocktick_queue_minmax'; 'pos_trigger_queue_minmax'};
    elseif length(strfind(lower(experi_names{i}),'mpc')) > 0
        type = 2;
        actor_methods = {'act_write'; 'mpc_action'; 'ang_trigger'; 'dis_clocktick'; 'pos_trigger'; 'mpc_action_queue_minmax';'ang_trigger_queue_minmax'; 'dis_clocktick_queue_minmax'; 'pos_trigger_queue_minmax'};
    end

    data = read_data(experi_date, experi_names{i}, actor_methods);

    plt_idx = 1;
    plt_idx = plot_ctrl_sigs(plt_idx, nbr_col,nbr_row,(i-1)*nbr_analy + plt_idx, data, type);
    %plt_idx = plot_cpu(plt_idx, nbr_col,nbr_row,(i-1)*nbr_analy + plt_idx,
    %data, type);
    %plt_idx = plot_node(plt_idx, nbr_col,nbr_row,(i-1)*nbr_analy + plt_idx, node_map, data, type);
    %plt_idx = plot_ctrl_error(plt_idx, nbr_col,nbr_row,(i-1)*nbr_analy +
    %plt_idx, data);
    plt_idx = plot_ctrl_mean_sq_error(plt_idx, nbr_col,nbr_row,(i-1)*nbr_analy + plt_idx, data, type);
    plt_idx = plot_e2e(plt_idx, nbr_col,nbr_row,(i-1)*nbr_analy + plt_idx, data, type);
    plt_idx = plot_exe_time(plt_idx, nbr_col,nbr_row,(i-1)*nbr_analy + plt_idx, data, type);
    plt_idx = plot_itr(plt_idx, nbr_col,nbr_row,(i-1)*nbr_analy + plt_idx, data, type);
    %plt_idx = plot_queue_sizes(plt_idx, nbr_col,nbr_row,(i-1)*nbr_analy +
    %plt_idx, data, type);
end
    
function data = read_data(experi_date, experi_name, actor_methods)
    files = fullfile('traces/', experi_date, experi_name, strcat(actor_methods,'.csv'));

    data = containers.Map;

    for i = 1:length(files)
        %disp(files{i})
        data(actor_methods{i}) = csvread(files{i});
    end
end

function plt_idx = plot_ctrl_sigs(plt_idx, col, row, fig_nbr, data, type)
    subplot(row, col, fig_nbr)
    hold on 
    grid on 
    
    ang = data('ang_trigger');
    pos = data('pos_trigger');
    dis = data('dis_clocktick');
    %interp_dis = interp1(dis(:,1), dis(:,2), pos(:,1));
    %plot(pos(:,1)-min_time, interp_dis)
    
    if type == 1; 
        inner = data('inner_cal_output');
        outer = data('outer_cal_output');
        min_time = min([inner(:,1); outer(:,1); ang(:,1); pos(:,1); dis(:,1)]);
    
        plot(ang(:,1)-min_time, ang(:,2))
        plot(pos(:,1)-min_time, pos(:,2))
        plot(dis(:,1)-min_time, dis(:,2))
        plot(inner(:,1)-min_time, inner(:,2))
        plot(outer(:,1)-min_time, outer(:,2))
        
        max_time = max([ ang(end,1)-min_time, pos(end,1)-min_time, dis(end,1)-min_time, inner(end,1)-min_time, outer(end,1)-min_time]);
        
        legend('Angle', 'Position', 'Set point', 'Inner ctrl. output', 'Outer ctrl. output')
    elseif type == 2;
        mpc = data('mpc_action');
        min_time = min([mpc(:,1); ang(:,1); pos(:,1); dis(:,1)]);
        
        plot(ang(:,1)-min_time, ang(:,2))
        plot(pos(:,1)-min_time, pos(:,2))
        plot(dis(:,1)-min_time, dis(:,2))
        plot(mpc(:,1)-min_time, mpc(:,2))
        
        max_time = max([ ang(end,1)-min_time, pos(end,1)-min_time, dis(end,1)-min_time, mpc(end,1)-min_time]);

        legend('Angle', 'Position', 'Set point', 'Ctrl. output')
    end
    
    xlabel('Time')
    ylabel('Voltage')
    
    ylim([-10 10])
    xlim([0 max_time])
    
    yticks([-10:2.5:10])
   
    plt_idx = plt_idx + 1;
end

function plt_idx = plot_node(plt_idx, col, row, fig_nbr, node_map, data, type)
    subplot(row, col, fig_nbr)
    hold on 
    grid on 
    
    if type == 1; 
        inner = data('inner_cal_output');
        outer = data('outer_cal_output');

        min_time = min([inner(:,1); outer(:,1)]);

        stairs(inner(:,1)-min_time, inner(:,end-1));
        stairs(outer(:,1)-min_time, outer(:,end-1));
        %plot(pos(:,1)-min_time, interp_dis)
        
        max_time = max([ ang(end,1)-min_time, pos(end,1)-min_time, dis(end,1)-min_time, inner(end,1)-min_time, outer(end,1)-min_time]);
   
        legend('Inner', 'Outer')
    elseif type == 2;
        mpc = data('mpc_action');
        
        min_time = min(mpc(:,1));

        stairs(mpc(:,1)-min_time, mpc(:,end-1));
   
        legend('MPC')
    end
    
    xlabel('Time')
    ylabel('Node')
    
    yticks(0:7)
    yticklabels()
    ylim([0 8])
    
    plt_idx = plt_idx + 1;
end

function plt_idx = plot_cpu(plt_idx, col, row, fig_nbr, data, type)
    subplot(row, col, fig_nbr)
    hold on 
    grid on 
    
    if type == 1; 
        inner = data('inner_cal_output');
        outer = data('outer_cal_output');

        min_time = min([inner(:,1); outer(:,1)]);

        stairs(inner(:,1)-min_time, inner(:,end));
        stairs(outer(:,1)-min_time, outer(:,end));
        %plot(pos(:,1)-min_time, interp_dis)
        
        legend('Inner', 'Outer')
    elseif type == 2;
        mpc = data('mpc_action');
        
        min_time = min(mpc(:,1));

        stairs(mpc(:,1)-min_time, mpc(:,end))
   
        legend('MPC')
    end
    
    xlabel('Time')
    ylabel('CPU nbr')
    
    yticks(0:3)
    ylim([0 3])
    
    plt_idx = plt_idx + 1;
end

function plt_idx = plot_queue_sizes(plt_idx, col, row, fig_nbr, data, type)
    subplot(row, col, fig_nbr)
    hold on 
    grid on 
    
    ang = data('ang_trigger_queue_minmax');
    pos = data('pos_trigger_queue_minmax');
    act = data('pos_trigger_queue_minmax');%data('act_write_queue_minmax');

    if type == 1; 
        inner = data('inner_cal_output_queue_minmax');
        outer = data('outer_cal_output_queue_minmax');
        
        min_time = min([inner(:,1); outer(:,1); ang(:,1); pos(:,1); act(:,1)]);
        max_val = max([inner(:,3); outer(:,3); ang(:,3); pos(:,3); act(:,3)]);
        
        plot(inner(:,1)-min_time, inner(:,3))
        plot(outer(:,1)-min_time, outer(:,3))
        plot(ang(:,1)-min_time, ang(:,3))
        plot(pos(:,1)-min_time, pos(:,3))
        plot(act(:,1)-min_time, act(:,3))
        
        legend('Inner', 'Outer', 'Angle', 'Position', 'Write')
    elseif type == 2;
        mpc = data('mpc_action_queue_minmax');
        
        min_time = min([mpc(:,1); ang(:,1); pos(:,1); act(:,1)]);
        max_val = max([mpc(:,3); ang(:,3); pos(:,3); act(:,3)]);

        plot(mpc(:,1)-min_time, mpc(:,3))
        plot(ang(:,1)-min_time, ang(:,3))
        plot(pos(:,1)-min_time, pos(:,3))
        plot(act(:,1)-min_time, act(:,3))
        
        legend('MPC', 'Angle', 'Position', 'Write')
    end
    
    ylim([0 max_val+1])
    
    yticks([0:1:max_val+1])
    
    xlabel('Time')
    ylabel('Queue backlog')
    
    plt_idx = plt_idx + 1;
end

function plt_idx = plot_ctrl_error(plt_idx, col, row, fig_nbr, data)
    subplot(row, col, fig_nbr)
    hold on 
    grid on 
    
    pos = data('pos_trigger');
    dis = data('dis_clocktick');
    
    min_time = min([pos(:,1); dis(:,1)]);
    
    interp_dis = interp1(dis(:,1), dis(:,2), pos(:,1));
    
    plot(pos(:,1)-min_time, (pos(:,2)-interp_dis))
    
    ylim([-10 10])
    yticks([-10:2.5:10])
    xlabel('Time')
    ylabel('Error (V)')
    
    plt_idx = plt_idx + 1;
end

function plt_idx = plot_ctrl_error_dist(plt_idx, col, row, fig_nbr, data)
    subplot(row, col, fig_nbr)
    hold on 
    grid on 
    
    pos = data('pos_trigger');
    dis = data('dis_clocktick');
    
    min_time = min([pos(:,1); dis(:,1)]);
    
    interp_dis = interp1(dis(:,1), dis(:,2), pos(:,1));
    
    ecdf((pos(:,2)-interp_dis));
    
    xlim([-10 10])
    xticks([-10:1:10])
    xlabel('Error (V)')
    ylabel('Prob.')
    
    plt_idx = plt_idx + 1;
end

function plt_idx = plot_ctrl_cum_error(plt_idx, col, row, fig_nbr, data)
    subplot(row, col, fig_nbr)
    hold on 
    grid on 
    
    pos = data('pos_trigger');
    dis = data('dis_clocktick');
    
    min_time = min([pos(:,1); dis(:,1)]);
    
    time = pos(:,1);
    interp_dis = interp1(dis(:,1), dis(:,2), pos(:,1));
    error = pos(:,2)-interp_dis;
    
    for idx = find(isnan(error))
        error(idx) = [];
        time(idx) = [];
    end
    
    cum_error = cumsum(error);
    
    plot(time-min_time, cum_error)
    
    xlabel('Time')
    ylabel('Cumulated error (V)')
    
    plt_idx = plt_idx + 1;
end

function plt_idx = plot_ctrl_mean_sq_error(plt_idx, col, row, fig_nbr, data, type)
    subplot(row, col, fig_nbr)
    hold on 
    grid on 
    
    pos = data('pos_trigger');
    dis = data('dis_clocktick');
    
    min_time = min([pos(:,1); dis(:,1)]);
    
    time = pos(:,1);
    interp_dis = interp1(dis(:,1), dis(:,2), pos(:,1));
    error = pos(:,2)-interp_dis;
    
    for idx = find(isnan(error))
        error(idx) = [];
        time(idx) = [];
    end
    
    mse_error = movmean(error.^2, 10);
    
    semilogy(time-min_time, mse_error)
    
    if type == 1; 
    elseif type == 2;
        mpc = data('mpc_action');
        disp(strcat('  ','MSE'))
        [the_upp, the_mean, the_low] = map_to_placement_mean( mpc(:,1), mpc(:,end-1), time, mse_error);
        semilogy(the_upp(:,1), the_upp(:,2))
        semilogy(the_mean(:,1), the_mean(:,2))
        semilogy(the_low(:,1), the_low(:,2))
        
        legend('MPC', '75th', 'Mean', '25th')
    end
    
    xlabel('Time')
    ylabel('Mean squared error (V)')
    
    plt_idx = plt_idx + 1;
end

function plt_idx = plot_e2e(plt_idx, col, row, fig_nbr, data, type)
    subplot(row, col, fig_nbr)
    hold on 
    e2e = data('act_write');
    
    min_time = min(e2e(:,1));
    
    mean_vals = mean([e2e(:,3),e2e(:,4),e2e(:,5)],2);
    the_diff = (e2e(:,2)-mean_vals)*1000;
    
    semilogy(e2e(:,1)-min_time, the_diff);
    grid on 
    
    if type == 1; 
    elseif type == 2;
        mpc = data('mpc_action');
        disp(strcat('  ','E2E'))
        [the_upp, the_mean, the_low] = map_to_placement_mean( mpc(:,1), mpc(:,end-1), e2e(:,1), the_diff);
        semilogy(the_upp(:,1), the_upp(:,2));
        semilogy(the_mean(:,1), the_mean(:,2));
        semilogy(the_low(:,1), the_low(:,2));
        
        legend('MPC', '75th', 'Mean', '25th')
    end
    
    %yticks([0,50,100,200,400,800,1600])
    
    xlabel('Time')
    ylabel('End-to-end latency')
    
    plt_idx = plt_idx + 1;
end

function plt_idx = plot_exe_time(plt_idx, col, row, fig_nbr, data, type)
    subplot(row, col, fig_nbr)
    hold on 
    grid on 
    
    if type == 1; 
    elseif type == 2;
        mpc = data('mpc_action');
        
        min_time = min([mpc(:,1)]);

        plot(mpc(:,1)-min_time, mpc(:,4)*1000);
        disp(strcat('  ','EXE'))
        [the_upp, the_mean, the_low] = map_to_placement_mean( mpc(:,1), mpc(:,end-1), mpc(:,1), mpc(:,4)*1000);
        plot(the_upp(:,1), the_upp(:,2));
        plot(the_mean(:,1), the_mean(:,2));
        plot(the_low(:,1), the_low(:,2));
        
        legend('MPC', '75th', 'Mean', '25th')
    end
    
    xlabel('Time')
    ylabel('Execution time (ms)')
    
    plt_idx = plt_idx + 1;
end

function plt_idx = plot_itr(plt_idx, col, row, fig_nbr, data, type)
    subplot(row, col, fig_nbr)
    hold on 
    grid on 
    
    if type == 1;
    elseif type == 2;
        mpc = data('mpc_action');
        
        min_time = min([mpc(:,1)]);

        plot(mpc(:,3));
        
        disp(strcat('  ','ITR'))
        [the_upp, the_mean, the_low] = map_to_placement_mean( mpc(:,1), mpc(:,end-1), mpc(:,1), mpc(:,3));
        plot(the_upp(:,1), the_upp(:,2));
        plot(the_mean(:,1), the_mean(:,2));
        plot(the_low(:,1), the_low(:,2));
         
        legend('MPC', '75th', 'Mean', '25th')
    end
    
%     xlabel('Time')
%     ylabel('Nbr iterations')
   
    plt_idx = plt_idx + 1;

end

% Helper functions
function [the_upp, the_mean, the_low] = map_to_placement_mean(p_t, p_d, t_t, t_d)
    node_map = {'Unknown', 'RP-1', 'RP-2', 'RP-3', 'RP-4', 'Edge-1', 'DC-1', 'AWS-EUC1'};
    idexs = [find(diff(p_d))' length(p_d)];
    min_time = min([p_t;t_t]);
    prev_t = 0;
    t_t = t_t - min_time;
    p_t = p_t - min_time;

    the_upp = [];
    the_mean  = [];
    the_low = [];
    
    for i = 1:length(idexs)
        t_frontier = p_t(idexs(i));
        idx = find(t_t>=prev_t & t_t<t_frontier);
        target_data = t_d(idx);
        
        
        the_upp =[the_upp; t_t(idx) , ones(length(idx),1,1)*prctile(target_data,75)];
        the_mean =[the_mean; t_t(idx) , ones(length(idx),1,1)*mean(target_data)];
        the_low =[the_low; t_t(idx) , ones(length(idx),1,1)*prctile(target_data,25)];
        
        disp(strcat('  - ', node_map{p_d(idexs(i))+1},' - median=',num2str(mean(target_data)),', lower quartile=',num2str(prctile(target_data,25)),', upper quartile=',num2str(prctile(target_data,75)),', upper whisker=',num2str(max(target_data)),', lower whisker=',num2str(min(target_data))))

        prev_t = t_frontier;
    end

end