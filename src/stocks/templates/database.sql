CREATE TABLE public.stocks (
	code varchar NOT NULL,
	"name" varchar NULL,
	last_price float4 NULL DEFAULT 0.0,
	nb int2 NULL DEFAULT 0,
	sell_price float4 NULL DEFAULT 0.0,
	buy_price float4 NULL DEFAULT 0.0,
	currency varchar NULL,
	exchange varchar NULL,
	"timestamp" timestamp NULL DEFAULT now(),
	active bool NOT NULL DEFAULT true,
	id serial4 NOT NULL,
	etf bool NOT NULL DEFAULT false,
	link varchar NULL,
	CONSTRAINT stocks_pk PRIMARY KEY (id)
);