"""
Miscellaneous utility functions for smokescreen tests
"""

import os
import re
import time
import uuid
import requests

# Selenium imports
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

from selenium.common.exceptions import NoSuchElementException

# Project imports
import config


def launch_driver(
        driver_name=None,
        desired_capabilities={},
        wait_time=config.selenium_wait_time):
    """Create and configure a WebDriver.
    
    Args:
        driver_name : Name of WebDriver to use
        wait_time : Time to implicitly wait for element load

    """

    driver_name = driver_name or config.driver_name
    
    driver_cls = getattr(webdriver, driver_name)


    if driver_name == 'Remote':

        # Set up command executor
        command_executor = 'http://%s:%s@ondemand.saucelabs.com:80/wd/hub' \
            % (os.environ.get('SAUCE_USERNAME'), os.environ.get('SAUCE_ACCESS_KEY'))

        driver = driver_cls(
            desired_capabilities=desired_capabilities,
            command_executor=command_executor
        )

    elif driver_name == 'PhantomJS':

        driver = driver_cls('/usr/local/bin/phantomjs')


    else:
            
        driver = driver_cls()
    
    # Wait for elements to load
    driver.implicitly_wait(wait_time)
    
    # Return driver
    return driver

def clear_text(elm):
    """Clear text via backspace. Usually we can skip
    this and clear via elm.clear() directly, but this
    doesn't work in all cases (e.g. Wiki editing).

    """
    
    for _ in range(len(elm.text)):
        elm.send_keys(Keys.BACK_SPACE)

def get_alert_boxes(driver, alert_text):
    """Check page for alert boxes. Asserts that there is exactly
    one matching alert.

    Args:
        driver : WebDriver instance
        alert_text : Text to search for in alert box
    Returns:
        matching alert boxes

    """

    # Find alerts
    alerts = driver.find_elements_by_xpath(
        '//*[text()[contains(translate(., "%s", "%s"), "%s")]]' %
        (alert_text.upper(), alert_text.lower(), alert_text.lower())
    )

    # Return matching alert boxes
    return alerts
    
find_btn = lambda elm: elm.find_element_by_xpath('.//button')


def fill_form(
        root, 
        fields, 
        button_finder=find_btn):
    """Fill out form fields and click submit button.

    Args:
        form : root element
        fields : dict of id -> value pairs for form
        button_finder : function to get button from root element

    """
    # Enter field values
    for field in fields:
        root.find_element_by_css_selector(field).send_keys(fields[field])
    
    # Click submit button
    button_finder(root).click()

def login(driver, username, password):
    """Login to OSF

    Args:
        driver : selenium.webdriver instance
        login_data : dict of id -> value pairs for login form

    Examples:
        > login(driver, {'username' : 'test@test.test', 'password' : 'testtest'})

    """

    # Browse to OSF login page
    driver.get('%s/account' % (config.osf_home))

    # Get login form
    login_form = driver.find_element_by_xpath('//form[@name="signin"]')
    fill_form(login_form, {
        '#username' : username,
        '#password' : password,
    })

def gen_user_data(_length=12):
    """ Generate data to create a user account. """

    uid = unicode(uuid.uuid1())[:_length - 1]
    unique = uid + u'\xe4'


    username = u'{}@osftest.org'.format(uid)

    return {
        'username': username,
        'username2': username,
        'password': unique,
        'password2': unique,
        'fullname': unique
    }

def create_user(driver=None, user_data=None):
    """Create a new user account.

    Args:
        driver : selenium.webdriver instance
        user_data : dict of id -> value pairs for registration form
                    default: config.registration_data
    Returns:
        dict of user information

    Examples:
        > create_user(driver, {
            'fullname' : 'test test',
            'username' : 'test@test.com',
            'username2' : 'test@test.com',
            'password' : 'testtest',
            'password2' : 'testtest',
        }

    """
    user_data = user_data or gen_user_data()

    requests.post(
        url='/'.join((config.osf_home.strip('/'), 'register/')),
        data={
            'register-fullname': user_data['fullname'],
            'register-username': user_data['username'],
            'register-username2': user_data['username'],
            'register-password': user_data['password'],
            'register-password2': user_data['password'],
        },
        verify=False
    )

    # Return user data
    return user_data

def goto_dashboard(driver):

    """Browse to dashboard page.
    
    Args:
        driver : WebDriver instance

    """
    driver.get('%s/dashboard' % (config.osf_home))

def goto_profile(driver):
    """Browse to public profile page. 
    
    Args:
        driver : WebDriver instance
    
    """
    # Browse to dashboard
    goto_dashboard(driver)

    # Click Public Profile link
    driver.find_element_by_link_text('My Public Profile').click()


def goto_project(driver, project_title=config.project_title):

    """Browse to project page.

    Args:
        driver : WebDriver instance
        project_title : Title of project to be loaded
    Returns:
        URL of project page

    """
    # Browse to dashboard
    goto_dashboard(driver)

    # Click on project title
    driver.find_element_by_link_text(project_title).click()
    return driver.current_url

def goto_files(driver, project_title=config.project_title):
    """ Browse to files page.

    Args:
        driver: WebDriver instance
        project_title : Title of project to be loaded
    """
    # Browse to project page
    goto_project(driver, project_title)

    # Browse to files page
    driver.find_element_by_link_text('Files').click()
    
def goto_settings(driver, project_name=config.project_title):
    """Browse to project settings page.

    Args:
        driver : WebDriver instance
        project_name : Project name

    """
    # Browse to project page
    goto_project(driver, project_name)

    # Click Settings button
    driver.find_element_by_link_text('Settings').click()

def goto_registrations(driver, project_name=config.project_title):
    
    # Browse to project page
    goto_project(driver, project_name)
    
    # Click Registrations button
    driver.find_element_by_link_text('Registrations').click()

def logout(driver):
    """ Log out of OSF.

    Args:
        driver : selenium.webdriver instance

    """
    # browse to OSF page
    driver.get(config.osf_home)

    # locate and click logout button
    try:
        driver.find_element_by_xpath('//a[@href="/logout"]').click()
    except NoSuchElementException:
        # There is no logout link - assume the user is not logged in
        pass

def create_project(driver, project_title=config.project_title, project_description=config.project_description):
    """Create new project

    Args:
        driver : selenium.webdriver instance
        project_title : project title
        project_description : project description
    Returns:
        URL of created project

    """
    # Browse to dashboard
    goto_dashboard(driver)

    # Click New Project button
    driver.find_element_by_link_text("New Project").click()

    # Fill out form and submit
    project_form = driver.find_element_by_xpath('//form[@name="newProject"]')
    fill_form(
        project_form, {
            '#title' : project_title,
            '#description' : project_description,
        }
    )

    # Return project URL
    return driver.current_url

def create_node(
        driver, 
        project_title=config.project_title, 
        node_title=config.node_title,
        project_url=None):
    """

    """
    # Browse to project
    if project_url is not None:
        driver.get(project_url)
    else:
        goto_project(driver, project_title)
    
    # Click New Node button
    driver.find_element_by_link_text('Add Component').click()
    
    # Get form
    form = driver.find_element_by_xpath(
        '//form[contains(@action, "newnode")]'
    )
    
    # Wait for modal to stop moving
    WebDriverWait(driver, 3).until(
        ec.visibility_of_element_located(
            (By.CSS_SELECTOR, 'input[name="title"]')
        )
    )
    
    # Fill out form
    fill_form(
        form, 
        {
            'input[name="title"]' : node_title,
            '#category' : 'Project',
        }
    )

def select_partial(driver, id, start, stop):
    """Select a partial range of text from an element.

    Args:
        driver : WebDriver instance
        id : ID of target element
        start : Start position
        stop : Stop position

    """
    # Inject partial selection function
    # Adapted from http://stackoverflow.com/questions/646611/programmatically-selecting-partial-text-in-an-input-field
    driver.execute_script('''
        (function(field, start, end) {
            if( field.createTextRange ) {
                var selRange = field.createTextRange();
                selRange.collapse(true);
                selRange.moveStart('character', start);
                selRange.moveEnd('character', end-start);
                selRange.select();
            } else if( field.setSelectionRange ) {
                field.setSelectionRange(start, end);
            } else if( field.selectionStart ) {
                field.selectionStart = start;
                field.selectionEnd = end;
            }
            field.focus();
        })(document.getElementById("%s"), %d, %d);
        ''' % (id, start, stop))

# Wiki functions
def edit_wiki(driver):
 
    edit_button = driver.find_element_by_link_text('Edit')
    edit_button.click()

def get_wiki_input(driver):
 
    return driver.find_element_by_id('wmd-input')

def add_wiki_text(driver, text):
 
    get_wiki_input(driver).send_keys(text)

def clear_wiki_text(driver):
 
    clear_text(get_wiki_input(driver))

def submit_wiki_text(driver):
    """ Click submit button. """

    driver.find_element_by_xpath(
        '//div[@class="wmd-panel"]//input[@type="submit"]'
    ).click()

def get_wiki_version(driver):
    """ Get current wiki version. """
 
    # Extract version text
    version = driver\
        .find_element_by_xpath('//dt[text()="Version"]/following-sibling::*')\
        .text
 
    # Strip (current) from version string
    version = re.sub('\s*\(current\)\s*', '', version, flags=re.I)

    # Return version number or 0
    try:
        return int(version)
    except ValueError:
        return 0

def get_wiki_par(driver):
    """ Get <p> containing wiki text. """

    # Set implicitly_wait to short value: text may not
    # exist, so we don't want to wait too long to find it
    driver.implicitly_wait(0.1)

    # Extract wiki text
    # Hack: Wiki text element isn't uniquely labeled,
    # so find its sibling first
    try:
        wiki_par = driver.find_element_by_xpath(
            '//div[@id="addContributors"]/following-sibling::div//p'
        )
    except NoSuchElementException:
        wiki_par = None

    # Set implicitly_wait to original value
    driver.implicitly_wait(config.selenium_wait_time)

    # Return element
    return wiki_par

def get_wiki_text(driver):
    """ Get text from wiki <p>. """

    # Get <p> containing wiki text
    wiki_par = get_wiki_par(driver)

    # Extract text
    if wiki_par is not None:
        return wiki_par.text
    return ''

def get_wiki_preview(driver):
    """
    """

    return driver\
        .find_element_by_id('wmd-preview')\
        .text

def forget_password(driver, email):
    """forgotpassword to OSF

    Args:
        driver : selenium.webdriver instance
        forgotpassword_data : dict of id -> value pairs for forgotpassword form

    Examples:
        > forgotpassword(driver, {'email' : 'test@test.test'})

    """

    # Browse to OSF forgotpassword page
    driver.get('%s/account' % (config.osf_home))

    # Get forgotpassword form
    forgotpassword_form = driver.find_element_by_xpath('//form[@name="forgotpassword"]')
    fill_form(forgotpassword_form, {
        '#forgot_password-email' : email,

    })


def project_rename(driver, text):

        driver.find_element_by_id('node-title-editable').click()

        # select the name field on the new popup
        edit_profile_name_field = driver.find_element_by_xpath(
            '//div[@class="popover-content"]//input[@class="span2"]'
        )

        # delete the curr
        # ent project name
        edit_profile_name_field.clear()

        # enter the new project name
        edit_profile_name_field.send_keys(text)

        # find and click submit new project name
        driver.find_element_by_xpath(
            '//div[@class="popover-content"]//button[@class="btn btn-primary"]'
        ).click()
        driver.refresh()





