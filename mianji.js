Function 面积();
Begin
    // 以下是参数
    day := IntToDate({day});
    time1_str := '{time1}';
    time2_str := '{time2}';
    num := {num};

    time1 := StrToTime(time1_str);
    time2 := StrToTime(time2_str);

    大盘分钟线 := get_zz1000_data(day, time1, time2);

    无涨停板股票列表 := array();
    有涨停板股票列表 := array();
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
            昨日30均线 := ref(ma(close(), 30), 1);
            前日30均线 := ref(ma(close(), 30), 2);
            if 昨日30均线 > 前日30均线 then
                均线向上 := 1;
            else
                均线向上 := 0;
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
        时间线 := data[:, '时间'];
        交叉点面积 := 计算交叉点和面积(stock_name, 时间线, 个股分钟线, 大盘分钟线);
        交叉点 := 交叉点面积[0];
        面积 := 交叉点面积[1];
        涨停板数1 := get_涨停板(stock_code, day, 1);
        涨停板数3 := get_涨停板(stock_code, day, 3);
        涨停板数5 := get_涨停板(stock_code, day, 5);
        涨停板数7 := get_涨停板(stock_code, day, 7);
        if 面积 <= 0 then
            continue;
        量比 := floatn(sum_vol / 前N日平均成交量 * 100, 2);
        买入量 := int(sum_vol / 10);
        买入价 := 计算买入价(stock_name, stock_code, day, data, 今日涨停价, 昨日收盘价, time2);

        开板 := 计算开板(stock_name, stock_code, day, 今日涨停价, 昨日收盘价, time1, 买入价[6]);
        开板次数 := 开板[0];
        最大开板回撤 := 开板[1];

        arr := array(('名称':stock_name, '代码':stock_code, '量比':量比,
            '上市天数':上市天数,'买入量':买入量, '是否涨停':是否涨停, '观察期收盘价涨幅': 收盘价涨幅, 'ma30向上':均线向上,
            '观察期结束可以直接买入':买入价[0], '观察期结束直接买入价':买入价[1],
            '大回撤开始时间':买入价[2], '大回撤结束时间':买入价[3], '大回撤买入价':买入价[4],
            '上一波谷形成时间': 买入价[5], '双波谷触发时间':买入价[6], '双波谷买入价':买入价[7], '双波谷涨幅':买入价[8],
            '双波谷前开板次数':开板次数, '双波谷前最大开板回撤':最大开板回撤,
            '交叉点':交叉点, '面积':面积, '1日涨停板数': 涨停板数1, '3日涨停板数':涨停板数3, '5日涨停板数':涨停板数5, '7日涨停板数':涨停板数7));
        if 涨停板数1 > 0 or 涨停板数3 > 0 or 涨停板数5 > 0 then
            有涨停板股票列表 &= arr;
        else
            无涨停板股票列表 &= arr;
    end
    SortTableByField(有涨停板股票列表, '面积', 0);
    SortTableByField(无涨停板股票列表, '面积', 0);
    ret &= 有涨停板股票列表;
    if length(ret) < num then
    begin
        ret &= 无涨停板股票列表[:num-length(ret)-1];
    end
    return exportjsonstring(ret);
End;

function 计算开板(stock_name, stock_code, day, 今日涨停价, 昨日收盘价, time1, 双波谷触发时间);
begin
    if 双波谷触发时间 = 0 then
        双波谷触发时间 := '15:00:00';

    with *,array(pn_Stock():stock_code, pn_date():day, pn_rate():2, pn_rateday():day, PN_Cycle():cy_1m()) do
    begin
        data := select
        TimeToStr(["date"]) as "时间",
        ["close"]
        from markettable datekey day+time1 to day+StrToTime(双波谷触发时间) of DefaultStockID() end;
    end

    开板次数 := 0;
    最大开板回撤 := 100;
    开板中 := 0;
    开板回撤 := 0;
    for idx := 1 to length(data) - 1 do
    begin
        if data[idx]['close'] < data[idx-1]['close'] then
        begin
            if data[idx-1]['close'] = 今日涨停价 then
            begin
                开板次数 += 1;
                开板中 := 1;
                开板回撤 := data[idx]['close'];
            end
            else if 开板中 = 1 then
                开板回撤 := data[idx]['close'];
        end
        else if data[idx]['close'] > data[idx-1]['close'] then
        begin
            if 开板中 then
            begin
                开板中 := 0;
                if 开板回撤 < 最大开板回撤 then
                    最大开板回撤 := 开板回撤;
            end
        end
    end
    if 开板中 then
    begin
        开板中 := 0;
        if 开板回撤 < 最大开板回撤 then
            最大开板回撤 := 开板回撤;
    end

    if 开板次数 = 0 then
        return array(0, 0);
    else
    begin
        ratio1 := count_ratio(今日涨停价, 昨日收盘价);
        ratio2 := count_ratio(最大开板回撤, 昨日收盘价);
        return array(开板次数, ratio1 - ratio2);
    end
end

function 计算交叉点和面积(stock_name, 时间线, 个股分钟线, 大盘分钟线);
begin
    if 个股分钟线[19] <= 大盘分钟线[19] then
        return array(0, 0);

    交叉点 := 0;
    for i := 18 downto 0 do
    begin
        if 个股分钟线[i] < 大盘分钟线[i] then
        begin
            交叉点 := i + 1;
            break;
        end
    end

    面积 := 0;
    for j := 交叉点 to 18 do
        面积 += ((个股分钟线[j] + 个股分钟线[j+1]) / 2 - (大盘分钟线[j] + 大盘分钟线[j+1]) / 2);

    交叉时间 := 0;
    if 交叉点 > 0 then
        交叉时间 := 时间线[交叉点];
    return array(交叉时间, floatn(面积, 2));
end

function 计算买入价(stock_name, stock_code, day, data, 今日涨停价, 昨日收盘价, time2);
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
    波峰波谷高度差 := 0.5;
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
    双波谷涨幅 := 0;
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

                if 双波谷触发时间 = 0 then // 已经触发双波谷就不需要再算了
                begin
                    if 下降幅度 >= 波峰波谷高度差 then
                    begin // 波谷形成
                        if 上一波谷收盘价 = 0 or count_ratio(上一波谷收盘价, data[i-1]['close']) < 波峰波谷高度差 then
                        begin // 第一个波谷或者双波谷之间跌幅没超过波峰波谷高度差
                            上一波谷形成时间 := data[i-1]['时间'];
                            上一波谷收盘价 := data[i-1]['close'];
                            上一波谷起始点 := data[下降起始点]['close'];
                        end
                        else
                        begin // 双波谷形成，条件是波谷本身跌幅超过波峰波谷高度差，双波谷之间跌幅超过波峰波谷高度差
                            双波谷触发时间 := data[i-1]['时间'];
                            双波谷买入价 := data[i-1]['close'];
                            双波谷涨幅 := count_ratio(data[i-1]['close'], 昨日收盘价);
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
        上一波谷形成时间, 双波谷触发时间, 双波谷买入价, 双波谷涨幅);
end
function get_涨停板(stock_code, day, num);
begin
    with *,array(pn_Stock():stock_code) do
    begin
        ret := 0;
        for i := 1 to num do
        begin
            one_day := StockEndTPrevNDay(day, i);
            if StockIsZt(one_day) then
                ret += 1;
        end
        return ret;
    end
end
function get_zz1000_data(day, time1, time2);
begin
    with *,array(pn_Stock():'SH000852', pn_date():day, pn_rate():2, pn_rateday():day, PN_Cycle():cy_day()) do
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
