Function 个股回撤();
Begin
    // 以下是参数
    day := IntToDate({day});
    begin_time_str := '{begin_time}';
    end_time_str := '{end_time}';

    min_high_ratio := 2;
    minutes := 5;

    // 以下是代码
    begin_time := StrToTime(begin_time_str);
    end_time := StrToTime(end_time_str);
    min_time := StrToTime("9:32:00");
    max_time := StrToTime("11:00:00");
    deltatime := StrToTime('00:01:00') * 2;

    time1 := begin_time - deltatime;
    time2 := end_time + deltatime;

    // 调试信息
    time1_str := TimeToStr(time1);
    time2_str := TimeToStr(time2);

    ret := array();
    stock_list := getbk('A股');

    stock_list::begin
        stock_code := mcell;
        stock_name := stockName(stock_code);

        if not (stock_code like 'SZ|SH') then
            continue;

        if stock_name like 'ST|退' then
            continue;


        if not is_trade_day(day, stock_code) then
            continue;

        // 计算昨日收盘价
        with *,array(pn_Stock():stock_code, pn_date():day, pn_rate():0, pn_rateday():0, PN_Cycle():cy_day()) do
        begin
            昨日收盘价 := floatn(ref(close(), 1), 3);
        end

        if 昨日收盘价 = 0 then
            continue;

        // 取分钟线信息
        with *,array(pn_Stock():stock_code, pn_date():day, pn_rate():0, pn_rateday():0, PN_Cycle():cy_1m()) do
        begin
            data := select
                TimeToStr(["date"]) as "时间",
                ['vol'],
                floatn(["close"], 3) as "close",
                floatn(['high'], 3) as 'high'
            from markettable datekey day+min_time to day+time2 of DefaultStockID() end;
        end

        // 计算大盘回撤前曾经的最高点
        曾经最高点 := vselect floatn(maxof(['close']), 3) from data where ['时间'] < TimeToStr(time1) end;
        曾经最高点涨幅 := count_ratio(曾经最高点, 昨日收盘价);
        if 曾经最高点涨幅 < min_high_ratio then
            continue;

        // 算量比
        sum_vol := vselect sumof(['vol'])from data end;
        with *,array(pn_Stock():stock_code, pn_date():day, pn_rate():0, pn_rateday():0, PN_Cycle():cy_day()) do
        begin
            前N日平均成交量 := ref(ma(vol(), 100), 1);
            量比 := floatn(sum_vol / 前N日平均成交量 * 100, 2);
        end

        // 过滤大盘回撤期间的分钟线数据
        data_回撤 := select * from data where ['时间'] >= time1_str end;

        // 计算回撤起点，终点，最低点
        观察期起点 := count_ratio(data_回撤[0]['close'], 昨日收盘价);
        观察期终点 := count_ratio(data_回撤[length(data_回撤)-1]['close'], 昨日收盘价);
        观察期最低点 := vselect count_ratio(minof(['close']), 昨日收盘价) from data end;

        if length(data_回撤) < 3 then
        begin
             最大回撤开始时间 := 0;
             最大回撤结束时间 := 0;
             最大回撤百分比 := 0;
             最大反向回撤开始时间 := 0;
             最大反向回撤结束时间 := 0;
             最大反向回撤百分比 := 0;
             次大反向回撤开始 := 0;
             次大反向回撤结束 := 0;
             次大反向回撤比 := 0;
        end
        else
        begin
            data_close := data_回撤[:,'close'];
            最大回撤 := MaxDrawDown(data_close, 0);
            最大回撤开始时间 := data_回撤[最大回撤[0]]['时间'];
            最大回撤结束时间 := data_回撤[最大回撤[1]]['时间'];
            最大回撤起点 := count_ratio(data_回撤[最大回撤[0]]['close'], 昨日收盘价);
            最大回撤终点 := count_ratio(data_回撤[最大回撤[1]]['close'], 昨日收盘价);
            最大回撤百分比 := floatn(最大回撤[3] * 100, 2);

            if length(data_回撤) > minutes then
            begin
                最大反向回撤 := MaxDrawDown(data_close, 1);
                最大反向回撤开始时间 := data_回撤[最大反向回撤[0]]['时间'];
                最大反向回撤结束时间 := data_回撤[最大反向回撤[1]]['时间'];
                最大反向回撤百分比 := floatn(最大反向回撤[3] * 100, 2);
            end
        end

        ret &= array(('名称':stock_name, '代码':stock_code, '量比':量比,
            '观察期开始时间':time1_str, '观察期结束时间':time2_str,
            '曾经最高点涨幅':曾经最高点涨幅, '观察期起点':观察期起点,
            '观察期终点':观察期终点, '观察期最低点':观察期最低点,
            '最大回撤开始时间':最大回撤开始时间, '最大回撤结束时间':最大回撤结束时间,
            '最大回撤起点':最大回撤起点, '最大回撤终点':最大回撤终点,
            '最大回撤百分比':最大回撤百分比,
            '最大反向回撤开始时间':最大反向回撤开始时间, '最大反向回撤结束时间':最大反向回撤结束时间,
            '最大反向回撤百分比':最大反向回撤百分比));
    end
    return exportjsonstring(ret);
End;

function count_ratio(value1, value2);
begin
    return floatn((value1 / value2 - 1) * 100, 3);
end

Function is_trade_day(day,stock_code);
Begin
    with *,array(pn_Stock():stock_code,PN_Date():day,pn_rate():0,pn_rateday():day,PN_Cycle():"日线") do
    begin
        if not spec(isTradeDay(day),stock_code) then
            return false;

        if IsStockGoDelistingPeriod(day) then
            return false;

        if IsST_3(day)=1 then
            return false
    end
    return true;
End;
