Function 面积2股票池();
Begin
    // 以下是参数
    day := IntToDate({day});
    time1_str := '{time1}';
    time2_str := '{time2}';
    time3_str := '{time3}';
    time4_str := '{time4}';
    num := {num};
    最小平均面积 := {min_avg_area};

    time1 := StrToTime(time1_str);
    time2 := StrToTime(time2_str);
    time3 := StrToTime(time3_str);
    time4 := StrToTime(time4_str);

    大盘分钟线 := get_zz1000_data(day, time1, time2);

    无涨停板股票列表1 := array();
    无涨停板股票列表2 := array();
    有涨停板股票列表1 := array();
    有涨停板股票列表2 := array();
    ret1 := array();
    ret2 := array();
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
            前N日平均成交量 := ref(ma(vol(), 100), 1);
            上市日 := FundGoMarketDate();
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
        assert(length(data) = 21);

        if data[20]['close'] = 今日涨停价 then
            continue;

        个股分钟线 := data[:, 'close'];
        for idx in 个股分钟线 do
        begin
            个股分钟线[idx] := count_ratio(个股分钟线[idx], 昨日收盘价);
        end

        // 计算量比
        sum_vol := 0;
        for i := 0 to 20 do
            sum_vol += data[i]['vol'];
        量比 := floatn(sum_vol / 前N日平均成交量, 2);

        时间线 := data[:, '时间'];
        交叉点面积 := 计算交叉点和面积(stock_name, 时间线, 个股分钟线, 大盘分钟线);
        交叉点 := 交叉点面积[0];
        总面积 := 交叉点面积[1];
        平均面积 := 交叉点面积[2];

        if 平均面积 < 最小平均面积 then
            continue;

        涨停板数1 := get_涨停板(stock_code, day, 1);
        涨停板数3 := get_涨停板(stock_code, day, 3);
        涨停板数5 := get_涨停板(stock_code, day, 5);
        涨停板数7 := get_涨停板(stock_code, day, 7);
        涨停板数10 := get_涨停板(stock_code, day, 10);

        买入价 := 计算买入价(stock_name, stock_code, day, 今日涨停价, time3, time4);

        开板 := 计算开板(stock_name, stock_code, day, 今日涨停价, 昨日收盘价, data);
        开板次数 := 开板[0];
        开板最大回撤 := 开板[1];

        day2 := day;
        while True do
        begin
            买入量 := 计算买入量(stock_name, stock_code, day2, time1, time2);
            if 买入量 = 0 then
            begin
                if day2 = IntToDate(上市日) then
                    break;
                else
                begin
                    with *,array(pn_Stock():stock_code, PN_Cycle():cy_day()) do
                    begin
                        day2 := StockEndTPrevNDay(day2, 1);
                    end
                end
            end
            else
                break;
        end

        最高价 := 0;
        最低价 := 今日涨停价;
        for i := 0 to 20 do
        begin
            if data[i]['close'] > 最高价 then
                最高价 := data[i]['close'];
            if data[i]['close'] < 最低价 then
                最低价 := data[i]['close'];
        end

        最高点 := count_ratio(最高价, 昨日收盘价);
        最低点 := count_ratio(最低价, 昨日收盘价);

        开盘最大回撤 := 计算开盘最大回撤(stock_name, stock_code, day, time2);

        arr := array(('名称':stock_name, '代码':stock_code, '量比':量比,
            '买入量':买入量, '买入价':买入价,
            '交叉点':交叉点, '总面积':总面积, '平均面积':平均面积,
            '1日涨停板数': 涨停板数1, '3日涨停板数':涨停板数3,
            '5日涨停板数':涨停板数5, '7日涨停板数':涨停板数7, '10日涨停板数':涨停板数10,
            '开板次数':开板次数, '开板最大回撤':开板最大回撤,
            '最高点':最高点, '最低点':最低点, '开盘最大回撤':开盘最大回撤));

        if 涨停板数1 > 0 or 涨停板数3 > 0 or 涨停板数5 > 0 or 涨停板数7 > 0 or 涨停板数10 > 0 then
        begin
            if stock_code[3:4] = '60' or stock_code[3:4] = '00' then
                有涨停板股票列表1 &= arr;
            else
                有涨停板股票列表2 &= arr;
        end
        else
        begin
            if stock_code[3:4] = '60' or stock_code[3:4] = '00' then
                无涨停板股票列表1 &= arr;
            else
                无涨停板股票列表2 &= arr;
        end
    end

    SortTableByField(无涨停板股票列表1, '平均面积', 0);
    SortTableByField(无涨停板股票列表2, '平均面积', 0);

    ret1 &= 有涨停板股票列表1;
    if length(ret1) < num then
    begin
        ret1 &= 无涨停板股票列表1[:num-length(ret1)-1];
    end

    ret2 &= 有涨停板股票列表2;
    if length(ret2) < num then
    begin
        ret2 &= 无涨停板股票列表2[:num-length(ret2)-1];
    end
    ret := array();
    ret &= ret1;
    ret &= ret2;
    return exportjsonstring(ret);
End;

function 计算开盘最大回撤(stock_name, stock_code, day, time2);
begin
    with *,array(pn_Stock():stock_code, pn_date():day, pn_rate():2, pn_rateday():day, PN_Cycle():cy_1m()) do
    begin
        data := select
        TimeToStr(["date"]) as "时间",
        ["close"]
        from markettable datekey day to day+time2 of DefaultStockID() end;
    end

    data_close := data[:, 'close'];
    最大跌幅 := MaxDrawDown(data_close, 0, 0);
    最大跌幅持续时间 := 最大跌幅[1] - 最大跌幅[0];
    最大跌幅开始时间 := data[最大跌幅[0]]['时间'];
    最大跌幅结束时间 := data[最大跌幅[1]]['时间'];
    最大跌幅百分比 := floatn(最大跌幅[3] * 100, 2);
    return 最大跌幅百分比;
end

function 计算买入量(stock_name, stock_code, day2, time1, time2);
begin
    with *,array(pn_Stock():stock_code, pn_date():day2, pn_rate():2, pn_rateday():day2, PN_Cycle():cy_day()) do
    begin
        当日涨停价 := StockZtClose(day2);
    end

    with *,array(pn_Stock():stock_code, pn_date():day2, pn_rate():2, pn_rateday():day2, PN_Cycle():cy_1m()) do
    begin
        day_data := select
        TimeToStr(["date"]) as "时间",
        ["close"],
        ['vol']
        from markettable datekey day2+time1 to day2+time2 of DefaultStockID() end;
    end

    剔除分钟 := array();
    剔除时长 := 5;
    for idx in day_data do
    begin
        if day_data[idx]['close'] = 当日涨停价 then
        begin
            if not (idx in 剔除分钟) then
                剔除分钟 &= array(idx);

            if idx <> 0 and day_data[idx-1]['close'] <> 当日涨停价 then
            begin
                // 封板
                j := 1;
                while idx - j >= 0 do
                begin
                    if not (idx - j in 剔除分钟) then
                        剔除分钟 &= array(idx - j);
                    j += 1;
                    if j > 剔除时长 then
                        break;
                end
            end

            if idx <> length(day_data) - 1 and day_data[idx+1]['close'] <> 当日涨停价 then
            begin
                // 开板
                j := 1;
                while idx + j <= length(day_data) - 1 do
                begin
                    if not (idx + j in 剔除分钟) then
                        剔除分钟 &= array(idx + j);
                    j += 1;
                    if j > 剔除时长 then
                        break;
                end
            end
        end
    end

    data_vol := array();
    for idx in day_data do
    begin
        if idx in 剔除分钟 then
            continue;

        data_vol &= array(day_data[idx]['vol']);
        num_vol += 1;
    end

    if num_vol < 剔除时长 then
        return 0;

    sortarray(data_vol);
    num_vol := int(length(data_vol) / 2);
    if num_vol = 0 then
        num_vol := 1;
    sum_vol := 0;
    for i := 0 to num_vol - 1 do
        sum_vol += data_vol[i];
    return int(sum_vol / num_vol);
end

function 计算开板(stock_name, stock_code, day, 今日涨停价, 昨日收盘价, data);
begin
    开板次数 := 0;
    开板后最低价 := 今日涨停价;
    for idx := 1 to length(data) - 1 do
    begin
        if data[idx]['close'] < data[idx-1]['close'] then
        begin
            if data[idx-1]['close'] = 今日涨停价 then
                开板次数 += 1;
        end

        if 开板次数 > 0 and data[idx]['close'] < 开板后最低价 then
            开板后最低价 := data[idx]['close'];
    end

    if 开板次数 = 0 then
        return array(0, 0);
    else
    begin
        ratio1 := count_ratio(今日涨停价, 昨日收盘价);
        ratio2 := count_ratio(开板后最低价, 昨日收盘价);
        return array(开板次数, floatn(ratio1 - ratio2, 2));
    end
end

function 计算买入价(stock_name, stock_code, day, 今日涨停价, time3, time4);
begin
    买入区间 := 5;
    with *,array(pn_Stock():stock_code, pn_date():day, pn_rate():2, pn_rateday():day, PN_Cycle():cy_1m()) do
    begin
        data := select
        TimeToStr(["date"]) as "时间",
        ["close"]
        from markettable datekey day+time3 to day+time4 of DefaultStockID() end;
    end
    assert(length(data) = 买入区间);

    sum_price := 0;
    num_price := 0;
    for i := 0 to 买入区间 - 1 do
    begin
        sum_price += data[i]['close'];
        num_price += 1;
    end
    return floatn(sum_price / num_price, 2);
end

function 计算交叉点和面积(stock_name, 时间线, 个股分钟线, 大盘分钟线);
begin
    flag := 0;
    if 个股分钟线[20] < 大盘分钟线[20] then
        flag := -1;
    else if 个股分钟线[20] > 大盘分钟线[20] then
        flag := 1;

    交叉点 := 0;
    for i := 19 downto 0 do
    begin
        if 个股分钟线[i] < 大盘分钟线[i] then
        begin
            if flag >= 0 then
            begin
                交叉点 := i + 1;
                break;
            end
        end
        else if 个股分钟线[i] > 大盘分钟线[i] then
        begin
            if flag <= 0 then
            begin
                交叉点 := i + 1;
                break;
            end
        end
    end

    if 交叉点 = 20 then
        return array(0,0,0);

    面积 := 0;
    for j := 交叉点 to 19 do
        面积 += ((个股分钟线[j] + 个股分钟线[j+1]) / 2 - (大盘分钟线[j] + 大盘分钟线[j+1]) / 2);

    交叉时间 := 0;
    平均面积 := floatn(面积 / (20 - 交叉点), 2);
    if 交叉点 > 0 then
        交叉时间 := 时间线[交叉点];
    return array(交叉时间, floatn(面积, 2), 平均面积);
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
    assert(length(data) = 21);
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
