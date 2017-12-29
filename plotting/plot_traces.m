close all

experi_date = '20171222';
experi_names = {'Wired_PID_inPoutP','Wired_PID_inDoutD','Wired_PID_inAoutA'};

nbr_experis = length(experi_names);
nbr_analy = 7;



for i = 1:nbr_experis
    if length(strfind(experi_names{i},'PID')) > 0 
        type = 1;
        script_name = 'bab_pid';
        actor_methods = {'inner_cal_output'; 'outer_cal_output'; 'ang_trigger'; 'dis_clocktick'; 'pos_trigger'; 'inner_cal_output_queue_minmax'; 'outer_cal_output_queue_minmax';'ang_trigger_queue_minmax'; 'dis_clocktick_queue_minmax'; 'pos_trigger_queue_minmax'};
    elseif length(strfind(experi_names{i},'MPC')) > 0
        type = 2
        script_name = 'bab_mpc';
        actor_methods = {'mpc_action'; 'ang_trigger'; 'dis_clocktick'; 'pos_trigger'; 'mpc_action_queue_minmax';'ang_trigger_queue_minmax'; 'dis_clocktick_queue_minmax'; 'pos_trigger_queue_minmax'};
    end

    data = read_data(experi_date, experi_names{i}, script_name, actor_methods);

    plot_ctrl_sigs( nbr_analy,nbr_experis,(i-1)*nbr_analy + 1, data, type)
    plot_cpu( nbr_analy,nbr_experis,(i-1)*nbr_analy + 2, data, type)
    plot_queue_sizes( nbr_analy,nbr_experis,(i-1)*nbr_analy + 3, data, type)
    plot_node( nbr_analy,nbr_experis,(i-1)*nbr_analy + 4, data, type)
    plot_ctrl_error( nbr_analy,nbr_experis,(i-1)*nbr_analy + 5, data)
    plot_ctrl_error_dist( nbr_analy,nbr_experis,(i-1)*nbr_analy + 6, data)
    plot_e2e( nbr_analy,nbr_experis,(i-1)*nbr_analy + 7, data)
end
    
function data = read_data(experi_date, experi_name, script_name, actor_methods)
    files = fullfile('traces/', experi_date, experi_name, strcat(script_name,'_',actor_methods,'.csv'));

    data = containers.Map;

    for i = 1:length(files)
        data(actor_methods{i}) = csvread(files{i});
    end
end

function plot_ctrl_sigs(col, row, fig_nbr, data, type)
    subplot(row, col, fig_nbr)
    hold on 
    grid on 
    
    ang = data('ang_trigger');
    pos = data('pos_trigger');
    dis = data('dis_clocktick');
    %interp_dis = interp1(dis(:,1), dis(:,2), pos(:,1));
    
    min_time = min([ang(:,1); pos(:,1); dis(:,1)]);
    
    plot(ang(:,1)-min_time, ang(:,2))
    plot(pos(:,1)-min_time, pos(:,2))
    plot(dis(:,1)-min_time, dis(:,2))
    %plot(pos(:,1)-min_time, interp_dis)
    
    xlabel('Time (ms)')
    ylabel('Voltage')
    
    ylim([-10 10])
    
    legend('Angle', 'Position', 'Set point')
end

function plot_node(col, row, fig_nbr, data, type)
    subplot(row, col, fig_nbr)
    hold on 
    grid on 
    
    if type == 1 
        inner = data('inner_cal_output');
        outer = data('outer_cal_output');

        min_time = min([inner(:,1); outer(:,1)]);

        stairs(inner(:,1)-min_time, inner(:,end-1))
        stairs(outer(:,1)-min_time, outer(:,end-1))
        %plot(pos(:,1)-min_time, interp_dis)
        
        legend('Inner', 'Outer')
    elseif type == 2
        mpc = data('mpc_action')
        
        min_time = min(mpc(:,1));

        stairs(mpc(:,1)-min_time, mpc(:,end-1))
   
        legend('MPC')
    end
    
    xlabel('Time (ms)')
    ylabel('Node')
    
    yticks(0:7)
    yticklabels({'Unknown', 'Plant 1', 'Plant 2', 'Plant 3', 'Plant 4', 'Edge', 'EDC', 'AWS'})
    ylim([0 8])
    
    
end

function plot_cpu(col, row, fig_nbr, data, type)
    subplot(row, col, fig_nbr)
    hold on 
    grid on 
    
    if type == 1 
        inner = data('inner_cal_output');
        outer = data('outer_cal_output');

        min_time = min([inner(:,1); outer(:,1)]);

        stairs(inner(:,1)-min_time, inner(:,end))
        stairs(outer(:,1)-min_time, outer(:,end))
        %plot(pos(:,1)-min_time, interp_dis)
        
        legend('Inner', 'Outer')
    elseif type == 2
        mpc = data('mpc_action')
        
        min_time = min(mpc(:,1));

        stairs(mpc(:,1)-min_time, mpc(:,end))
   
        legend('MPC')
    end
    
    xlabel('Time (ms)')
    ylabel('CPU nbr')
    
    yticks(0:3)
    ylim([0 3])
    
    legend('Inner', 'Outer')
end

function plot_queue_sizes(col, row, fig_nbr, data, type)
    subplot(row, col, fig_nbr)
    hold on 
    grid on 
    
    if type == 1 
        inner = data('inner_cal_output');
        outer = data('outer_cal_output');

        min_time = min([inner(:,1); outer(:,1)]);

        stairs(inner(:,1)-min_time, inner(:,3))
        stairs(outer(:,1)-min_time, outer(:,3))
        %plot(pos(:,1)-min_time, interp_dis)
        
        legend('Inner', 'Outer', 'Angle', 'Position', 'Write')
        
        min_times = [inner(:,1); outer(:,1)];
    elseif type == 2
        mpc = data('mpc_action')
        
        min_time = min(mpc(:,1));

        stairs(mpc(:,1)-min_time, mpc(:,3))
   
        legend('MPC', 'Angle', 'Position', 'Write')
        
        min_times = [mpc(:,1)];
    end
    
    ang = data('ang_trigger_queue_minmax');
    pos = data('pos_trigger_queue_minmax');
    act = data('pos_trigger_queue_minmax');%data('act_write_queue_minmax');
    
    min_time = min([min_times; ang(:,1); pos(:,1); act(:,1)]);
    
    stairs(ang(:,1)-min_time, ang(:,3))
    stairs(pos(:,1)-min_time, pos(:,3))
    stairs(act(:,1)-min_time, act(:,3))
    
    xlabel('Time (ms)')
    ylabel('Queue backlog')
end

function plot_ctrl_error(col, row, fig_nbr, data)
    subplot(row, col, fig_nbr)
    hold on 
    grid on 
    
    pos = data('pos_trigger');
    dis = data('dis_clocktick');
    
    min_time = min([pos(:,1); dis(:,1)]);
    
    interp_dis = interp1(dis(:,1), dis(:,2), pos(:,1));
    
    plot(pos(:,1)-min_time, (pos(:,2)-interp_dis))
    
    ylim([-10 10])
    
    xlabel('Time (ms)')
    ylabel('Error (V)')
end

function plot_ctrl_error_dist(col, row, fig_nbr, data)
    subplot(row, col, fig_nbr)
    hold on 
    grid on 
    
    pos = data('pos_trigger');
    dis = data('dis_clocktick');
    
    min_time = min([pos(:,1); dis(:,1)]);
    
    interp_dis = interp1(dis(:,1), dis(:,2), pos(:,1));
    
    ecdf((pos(:,2)-interp_dis))
    
    xlim([-10 10])
    
    xlabel('Error (V)')
    ylabel('Prob.')
end

function plot_ctrl_cum_error(col, row, fig_nbr, data)
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
    
    xlabel('Time (ms)')
    ylabel('Cumulated error (V)')
end

function plot_e2e(col, row, fig_nbr, data)
    subplot(row, col, fig_nbr)
    e2e = data('act_write');
    
    min_time = min(e2e(:,1));
    
    mean_vals = mean([e2e(:,3),e2e(:,4),e2e(:,5)],2);
    the_diff = (e2e(:,2)-mean_vals)*1000;
    
    plot(e2e(:,1)-min_time, the_diff)
    grid on 
    
    xlabel('Time (ms)')
    ylabel('End-to-end latency')
end