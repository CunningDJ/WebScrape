from bs4 import BeautifulSoup
from urllib2 import urlopen, quote, HTTPError
from PIL import Image
import cStringIO
from os import path, mkdir, makedirs
import urlparse as up
from threading import Thread

from Queue import Queue

try:
    pwd = path.dirname(__file__)
except NameError:
    pwd = path.dirname('.')

DEBUG = True

def debug(message):
    if DEBUG:
        print(message)

def main():
    '''
    ## WASHINGTON POST ##
    "https://www.washingtonpost.com/"

    ## ART DAILY ##
    'http://artdaily.com'

    ## EXHIBIT-E ##
    'http://www.exhibit-e.com/'
    '''

    ## url to be procesed ##
    #TARGET_URL = 'http://www.deviantart.com/'
    web_scraper_q = Queue()
    site_query_gui(web_scraper_q)


def site_query_gui(web_scraper_q):
    import Tkinter as tk
    site_query = tk.Tk()
    bg = 'lightblue'
    frame = tk.Frame(site_query, width=50, height=10, bg=bg, padx=10, pady=5)
    frame.pack(expand=True)

    label_var = tk.StringVar()
    which_url_label = tk.Label(frame, textvariable=label_var, bg=bg)
    which_url_label.pack(side=tk.TOP)
    label_var_default = "Which URL would you like to grab?"
    label_var.set(label_var_default)


    entry_stringvar = tk.StringVar()
    entry_box = tk.Entry(frame, textvariable=entry_stringvar)
    entry_box.pack(side=tk.TOP, expand=True, fill=tk.X)
    entry_stringvar.set('')

    def set_label(_str):
        label_var.set(_str)
        site_query.update_idletasks()

    def process_entry():
        url = entry_stringvar.get()
        if WebScraper.good_home_url(url):
            set_label(label_var_default + '\n' + 'OK! Processing...')
            web_scraper_q.put(url)
            web_scraper_q.join()
            set_label(label_var_default + '\n' + 'Done! Any more?')
        else:
            set_label(label_var_default + '\n' + 'Bad URL. Try Again.')
            print up.urlparse(url)

    button_bg = 'orange'
    enter_url_button = tk.Button(frame, text="Enter URL",
                                 command=process_entry, bg=button_bg)
    enter_url_button.pack(side=tk.TOP)

    def web_scrape_work(url_q):
        while True:
            url = url_q.get()

            ws = WebScraper(url)
            ws.download_images()
            # Indicates it is finished processing the q item (url), allowing the worker that
            # passed it to be freed of the join()
            url_q.task_done()

    web_scrape_worker = Thread(target=web_scrape_work, args=(web_scraper_q,))
    web_scrape_worker.setDaemon(True)
    web_scrape_worker.start()

    site_query.mainloop()


class WebScraper():

    def __init__(self, url):
        self.home_url = url
        name_counter = 0
        dump_folder = path.join(pwd, 'dump')
        while True:
            test_name = path.join(dump_folder, str(name_counter))
            if path.isdir(test_name):
                name_counter += 1
            else:
                dump_folder = test_name
                print("=======\nSaving images to {}\n=======".format(dump_folder))
                break
        self.dump_folder = dump_folder

        self.filepath_set = set()

    @staticmethod
    def good_home_url(_url):
        urlp = up.urlparse(_url)
        if '' in (urlp.netloc, urlp.scheme):
            return False

        try:
            urlopen(_url)
        except:
            raise
            return False

        return True

    @staticmethod
    def yes_to_request(_str):
        while True:
            resp = raw_input(_str).strip()
            if resp.lower() in ('n', 'no', 'nope', 'naw'):
                return False
            elif resp.lower() in ('y', 'yes', 'yeah', 'si', 'yup'):
                return True
            else:
                print("Incorrect input.  Need a yes or no respone.")

    @staticmethod
    def is_image_url(_url):
        if type(_url) is str:
            extension_options = ('.png', '.jpg', '.jpeg')
            extensions_tests = [_url.endswith(x) for x in extension_options]
            return True in extensions_tests
        else:
            return False

    def process_link(self, item_url, charset='utf-8'):
        parsed_url = up.urlparse(item_url)
        proc_url = item_url
        if parsed_url.netloc == '':
            proc_url = up.urljoin(self.home_url, item_url)
        '''
        if isinstance(proc_url, unicode):
            proc_url = proc_url.encode(charset, 'ignore')
            scheme, netloc, path, qs, anchor = up.urlsplit(proc_url)
            path = quote(path, '/%')
            return up.urlunsplit((scheme, netloc, path, qs, anchor))
        '''
        proc_url = quote(proc_url, safe="%/:=&?~#+!$,;'@()*[]")
        return proc_url


    def unique_filepath(self, _url, out_folder=None):
        if out_folder is None:
            out_folder = self.dump_folder
        # concats the given subpath/name with the out_folder
        def _path(_sub):
            return path.join(out_folder, _sub)

        def is_taken(_path):
            return _path in self.filepath_set or path.isfile(_path)

        # Not to be used for relative path conversion.
        # Just cleans up the '/\' path separators in the path strings
        def clean(_path):
            return path.abspath(_path)

        file_name = path.basename(_url)
        file_path = _path(file_name)
        if is_taken(file_path):
            counter = 1
            while True:
                file_base, ext = path.splitext(file_name)
                test_file_name = '{}.{}{}'.format(file_base, counter, ext)
                test_file_path = _path(test_file_name)
                if not is_taken(test_file_path):
                    self.filepath_set.add(test_file_path)
                    return clean(test_file_path)
                else:
                    counter += 1
        else:
            return clean(file_path)

    def download_images(self):
        '''
        Downloads all of the img items via the URL in their "src" field

        :return: paths of all of the downloaded image files
        '''
        yes_to = self.yes_to_request
        # Counts how many images have been saved.
        save_counter = 0

        site_fh = urlopen(self.home_url)
        site_content = site_fh.read()
        site_soup = BeautifulSoup(site_content, "lxml")
        imgs = site_soup.findAll("img")

        image_dump_folder = path.join(self.dump_folder, 'images')

        image_paths = []

        for item in imgs:
            src_url = item.get("src")
            if self.is_image_url(src_url):
                processed_url = self.process_link(src_url)
                debug('Image URL found:')
                debug('--------------')
                debug('raw url: {}'.format(src_url))
                debug('processed url: {}'.format(processed_url))
                try:
                    pic = Image.open(cStringIO.StringIO(urlopen(processed_url).read()))
                    save_path = self.unique_filepath(processed_url, image_dump_folder)
                    if not path.isdir(image_dump_folder):
                        makedirs(image_dump_folder)
                    pic.save(save_path)
                    image_paths.append(save_path)
                except HTTPError:
                    print("Error with url: [{}]".format(src_url))
                    raise

                debug("Saved: {}".format(save_path))
                save_counter += 1
                if save_counter % 100 == 0:
                    keep_scraping = "{} images scraped. Continue? ".format(save_counter)
                    if not yes_to(keep_scraping):
                        return image_paths
                debug('\n')

        debug('Images downloaded.')
        return image_paths


if __name__ == "__main__":
    main()
