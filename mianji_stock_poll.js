Function 面积2股票池();
Begin
    // 以下是参数
    day := IntToDate({day});
    time1_str := '{time1}';
    time2_str := '{time2}';
    time3_str := '{time3}';
    time4_str := '{time4}';
    num := {num};

    time1 := StrToTime(time1_str);
    time2 := StrToTime(time2_str);
    time3 := StrToTime(time3_str);
    time4 := StrToTime(time4_str);

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
        assert(length(data) = 21);

        观察期结束是否涨停 := 0;
        if data[20]['close'] = 今日涨停价 then
            观察期结束是否涨停 := 1;

        个股分钟线 := data[:, 'close'];
        for idx in 个股分钟线 do
        begin
            个股分钟线[idx] := count_ratio(个股分钟线[idx], 昨日收盘价);
        end

        // 计算买入量
        data_vol := select ['vol'] from data where ['close'] <> 今日涨停价 end;
        if length(data_vol) = 0 then
            买入量 := 0;
        else
        begin
            data_vol := data_vol[:, 'vol'];
            sortarray(data_vol);
            num_vol := int(length(data_vol) / 2);
            if num_vol = 0 then
                num_vol := 1;
            sum_vol := 0;

            for i := 0 to num_vol - 1 do
                sum_vol += data_vol[i];
            买入量 := int(sum_vol / num_vol);
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

        if 总面积 <= 0 then
            continue;

        平均面积 := 交叉点面积[2];

        涨停板数1 := get_涨停板(stock_code, day, 1);
        涨停板数3 := get_涨停板(stock_code, day, 3);
        涨停板数5 := get_涨停板(stock_code, day, 5);
        涨停板数7 := get_涨停板(stock_code, day, 7);

        买入价 := 计算买入价(stock_name, stock_code, day, 今日涨停价, time3, time4);

        arr := array(('名称':stock_name, '代码':stock_code, '量比':量比,
            '买入量':买入量, '买入价':买入价, '观察期结束是否涨停': 观察期结束是否涨停,
            '交叉点':交叉点, '总面积':总面积, '平均面积':平均面积,
            '1日涨停板数': 涨停板数1, '3日涨停板数':涨停板数3,
            '5日涨停板数':涨停板数5, '7日涨停板数':涨停板数7));


        if 涨停板数1 > 0 or 涨停板数3 > 0 or 涨停板数5 > 0 or 涨停板数7 > 0 then
            有涨停板股票列表 &= arr;
        else
            无涨停板股票列表 &= arr;
    end

    SortTableByField(无涨停板股票列表, '平均面积', 0);
    ret &= 有涨停板股票列表;
    if length(ret) < num then
    begin
        ret &= 无涨停板股票列表[:num-length(ret)-1];
    end
    return exportjsonstring(ret);
End;

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
    if 个股分钟线[20] <= 大盘分钟线[20] then
        return array(0, 0, 0);

    交叉点 := 0;
    for i := 19 downto 0 do
    begin
        if 个股分钟线[i] < 大盘分钟线[i] then
        begin
            交叉点 := i + 1;
            break;
        end
    end

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
