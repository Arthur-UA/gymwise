async function pageFunction(context) {
    const $ = context.jQuery;
    const results = [];

    context.log.info(`SCRAPING PAGE: ${context.request.url}`);

    $('a.w-full.border.rounded-xl.bg-white').each((_, element) => {
        const $el = $(element);

        const url = "https://www.jefit.com" + $el.attr('href')?.trim();
        const exerciseName = $el.find('p.text-xl\\/6').first().text().trim();
        const spans = $el.find('span.text-base\\/6');
        const muscleGroup = spans.eq(0).text().trim();
        const equipment = spans.eq(1).text().trim();
        const description = $el.find('p.text-sm\\/5').text().trim();
        const imageUrl = "https://www.jefit.com" + $el.find('img').attr('src')?.trim();

        context.log.info(`Done for URL: ${url}`);

        results.push({
            url,
            exerciseName,
            muscleGroup,
            equipment,
            description,
            imageUrl
        });
    });

    return results;
}