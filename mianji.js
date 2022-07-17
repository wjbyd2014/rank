Function 面积();
Begin
    // 以下是参数
    day := IntToDate({day});
    begin_time_str := '{begin_time}';
    end_time_str := '{end_time}';
    num := {num};

    time1 := StrToTime(begin_time_str);
    time2 := StrToTime(end_time_str);

    大盘分钟线 := get_zz1000_data(day, time1, time2);

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
        with *,array(pn_Stock():stock_code, pn_date():day, pn_rate():2, pn_rateday():day, PN_Cycle():cy_day()) do
        begin
            昨日收盘价 := ref(close(), 1);
            今日涨停价 := StockZtClose(day);
            上市天数 := StockGoMarketDays();
            前N日平均成交量 := ref(ma(vol(), 100), 1);
        end

        if 昨日收盘价 = 0 or 今日涨停价 = 0 then
            continue;

        // 获取分钟线
        with *,array(pn_Stock():stock_code, pn_date():day, pn_rate():2, pn_rateday():day, PN_Cycle():cy_1m()) do
        begin
            data := select
            TimeToStr(["date"]) as "时间",
            ["close"],
            ['vol']
            from markettable datekey day+time1 to day+time2 of DefaultStockID() end;
        end

        时间线 := data[:, '时间'];

        assert(length(data) = 20);

        是否涨停 := 0;
        if data[19]['close'] = 今日涨停价 then
            是否涨停 := 1;
        else if count_ratio(data[19]['close'], 昨日收盘价) > 10 then
            是否涨停 := 1;

        收盘价涨幅 := count_ratio(data[19]['close'], 昨日收盘价);

        个股分钟线 := data[:, 'close'];
        for idx in 个股分钟线 do
        begin
            个股分钟线[idx] := count_ratio(个股分钟线[idx], 昨日收盘价);
        end

        // 计算量比
        data_vol := data[:, 'vol'];
        sortarray(data_vol);
        sum_vol := 0;
        for i := 5 to 14 do
        begin
            sum_vol += data_vol[i];
        end

        交叉点面积 := 计算交叉点和面积(stock_name, 时间线, 个股分钟线, 大盘分钟线);
        交叉点 := 交叉点面积[0];
        面积 := 交叉点面积[1];

        量比 := floatn(sum_vol / 前N日平均成交量 * 100, 2);
        买入量 := int(sum_vol / 10);
        买入价 := 计算买入价(stock_name, stock_code, day, data, 今日涨停价, time2);
        arr := array(('名称':stock_name, '代码':stock_code, '量比':量比,
            '上市天数':上市天数,'买入量':买入量, '是否涨停':是否涨停, '收盘价涨幅': 收盘价涨幅,
            '观察期结束可以直接买入':买入价[0], '观察期结束直接买入价':买入价[1],
            '大回撤开始时间':买入价[2], '大回撤结束时间':买入价[3], '大回撤买入价':买入价[4],
            '上一波谷形成时间': 买入价[5], '双波谷触发时间':买入价[6], '双波谷买入价':买入价[7],
            '交叉点':交叉点, '面积':面积));
        ret &= arr;
    end
    SortTableByField(ret, '面积', 0);
    return exportjsonstring(ret[:num-1]);
End;

function 计算交叉点和面积(stock_name, 时间线, 个股分钟线, 大盘分钟线);
begin
    交叉点 := -1;
    for i := 18 downto 0 do
    begin
        if (个股分钟线[i] <= 大盘分钟线[i]) and (个股分钟线[i+1] > 大盘分钟线[i+1]) then
        begin
            if 个股分钟线[i] = 大盘分钟线[i] then
                交叉点 := i;
            else
                交叉点 := i + 1;
            break;
        end
    end

    面积 := 0;
    if 交叉点 >= 0 then
    begin
        for j := 交叉点 to 18 do
            面积 += ((个股分钟线[j] + 个股分钟线[j+1]) / 2 - (大盘分钟线[j] + 大盘分钟线[j+1]) / 2);
    end
    else
    begin
        for j := 0 to 18 do
        begin
            if 个股分钟线[i] > 大盘分钟线[i] then
                面积 += ((个股分钟线[j] + 个股分钟线[j+1]) / 2 - (大盘分钟线[j] + 大盘分钟线[j+1]) / 2);
        end
    end
    交叉时间 := 0;
    if 交叉点 >= 0 then
        交叉时间 := 时间线[交叉点];
    return array(交叉时间, floatn(面积, 2));
end

function 计算买入价(stock_name, stock_code, day, data, 今日涨停价, time2);
begin
    highest := data[0]['close'];
    lowest := data[0]['close'];
    for i := 1 to 18 do
    begin
        close_ := data[i]['close'];
        if close_ > highest then
            highest := close_;

        if close_ < lowest then
            lowest := close_;
    end

    threshold := (highest - lowest) * 0.2;
    diff_ := data[19]['close'] - lowest;
    if diff_ <= threshold and 今日涨停价 <> data[19]['close'] then
    begin
        观察期结束可以直接买入 := 1;
        观察期结束直接买入价 := data[19]['close'];
    end
    else
    begin
        观察期结束可以直接买入 := 0;
        观察期结束直接买入价 := 0;
    end

    with *,array(pn_Stock():stock_code, pn_date():day, pn_rate():2, pn_rateday():day, PN_Cycle():cy_1m()) do
    begin
        data := select
        TimeToStr(["date"]) as "时间",
        ["close"]
        from markettable datekey day+time2 to day+0.99999 of DefaultStockID() end;
    end

    下降起始点 := -1;
    下降起始时间 := 0;
    大回撤结束时间 := 0;
    大回撤开始时间 := 0;
    大回撤买入价 := 0;
    上一波谷起始点 := 0;
    上一波谷形成时间 := 0;
    上一波谷收盘价 := 0;
    双波谷触发时间 := 0;
    双波谷买入价 := 0;

    for i := 1 to length(data) - 1 do
    begin
        if data[i]['close'] < data[i-1]['close'] then
        begin
            if 下降起始点 = -1 then
            begin
                下降起始点 := i-1;
                下降起始时间 := data[i-1]['时间'];
            end
        end
        else if data[i]['close'] > data[i-1]['close'] then
        begin
            if 下降起始点 <> -1 then // 波谷形成
            begin
                下降幅度 := count_ratio(data[下降起始点]['close'], data[i-1]['close']);
                if 大回撤结束时间 = 0 and 下降幅度 > 1.5 then
                begin
                    大回撤开始时间 := data[下降起始点]['时间'];
                    大回撤结束时间 := data[i-1]['时间'];
                    大回撤买入价 := data[i-1]['close'];
                end

                if 双波谷触发时间 = 0 then // 已经触发双波谷了，不需要再算了
                begin
                    if 下降幅度 >= 0.5 then
                    begin // 波谷形成
                        if 上一波谷收盘价 = 0 then
                        begin // 第一个波谷
                            上一波谷形成时间 := data[i-1]['时间'];
                            上一波谷收盘价 := data[i-1]['close'];
                            上一波谷起始点 := data[下降起始点]['close'];
                        end
                        else if count_ratio(上一波谷收盘价, data[i-1]['close']) >= 0.5 then
                        begin // 双波谷形成，条件是波谷本身跌幅超过0.5，双波谷之间跌幅超过0.5，且当前波谷的高点不能比上个波谷的高点更高
                            if data[下降起始点]['close'] <= 上一波谷起始点 then
                            begin
                                双波谷触发时间 := data[i-1]['时间'];
                                双波谷买入价 := data[i-1]['close'];
                            end
                            else
                            begin // 当前波谷最高点比上个波谷高了，需要重新这个波谷为第一个波谷
                                上一波谷形成时间 := data[i-1]['时间'];
                                上一波谷收盘价 := data[i-1]['close'];
                                上一波谷起始点 := data[下降起始点]['close'];
                            end
                        end
                        else
                        begin // 双波谷之间跌幅没超过0.5，重置当前波谷为第一个波谷
                            上一波谷形成时间 := data[i-1]['时间'];
                            上一波谷收盘价 := data[i-1]['close'];
                            上一波谷起始点 := data[下降起始点]['close'];
                        end
                    end
                    else // 下降幅度太小，不算波谷，但需要重置上一波谷的信息
                    begin
                        上一波谷形成时间 := 0;
                        上一波谷收盘价 := 0;
                    end
                end
                下降起始点 := -1;
            end
        end
        if 大回撤结束时间 <> 0 and 双波谷触发时间 <> 0 then
            break;
    end

    if 双波谷触发时间 = 0 then
        上一波谷形成时间 := 0;

    return array(观察期结束可以直接买入, 观察期结束直接买入价, 大回撤开始时间, 大回撤结束时间, 大回撤买入价,
        上一波谷形成时间, 双波谷触发时间, 双波谷买入价);
end

function get_zz1000_data(day, time1, time2);
begin
    with *,array(pn_Stock():'SH000852', pn_date():day, pn_rate():0, pn_rateday():0, PN_Cycle():cy_day()) do
    begin
        大盘昨日收盘价 := ref(close(), 1);
    end

    // 获取分钟线
    with *,array(pn_Stock():'SH000852', pn_date():day, pn_rate():2, pn_rateday():day, PN_Cycle():cy_1m()) do
    begin
        data := select
        TimeToStr(["date"]) as "时间",
        ["close"]
        from markettable datekey day+time1 to day+time2 of DefaultStockID() end;
    end

    assert(length(data) = 20);

    data := data[:, 'close'];
    for idx in data do
    begin
        data[idx] := count_ratio(data[idx], 大盘昨日收盘价);
    end
    return data;
end

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
