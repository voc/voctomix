/*
 * GStreamer
 * Copyright (C) 2005 Thomas Vander Stichele <thomas@apestaart.org>
 * Copyright (C) 2005 Ronald S. Bultje <rbultje@ronald.bitfreak.net>
 * Copyright (C) 2014 Peter Körner <<user@hostname.org>>
 * 
 * Permission is hereby granted, free of charge, to any person obtaining a
 * copy of this software and associated documentation files (the "Software"),
 * to deal in the Software without restriction, including without limitation
 * the rights to use, copy, modify, merge, publish, distribute, sublicense,
 * and/or sell copies of the Software, and to permit persons to whom the
 * Software is furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
 * FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
 * DEALINGS IN THE SOFTWARE.
 *
 * Alternatively, the contents of this file may be used under the
 * GNU Lesser General Public License Version 2.1 (the "LGPL"), in
 * which case the following provisions apply instead of the ones
 * mentioned above:
 *
 * This library is free software; you can redistribute it and/or
 * modify it under the terms of the GNU Library General Public
 * License as published by the Free Software Foundation; either
 * version 2 of the License, or (at your option) any later version.
 *
 * This library is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * Library General Public License for more details.
 *
 * You should have received a copy of the GNU Library General Public
 * License along with this library; if not, write to the
 * Free Software Foundation, Inc., 59 Temple Place - Suite 330,
 * Boston, MA 02111-1307, USA.
 */

/**
 * SECTION:element-vocschnipselsink
 *
 * FIXME:Describe vocschnipselsink here.
 *
 * <refsect2>
 * <title>Example launch line</title>
 * |[
 * gst-launch -v -m fakesrc ! vocschnipselsink ! fakesink silent=TRUE
 * ]|
 * </refsect2>
 */

#ifdef HAVE_CONFIG_H
#  include <config.h>
#endif

#include <gst/gst.h>

#include "gstvocschnipselsink.h"

GST_DEBUG_CATEGORY_STATIC (gst_voc_schnipsel_sink_debug);
#define GST_CAT_DEFAULT gst_voc_schnipsel_sink_debug
#define DEFAULT_LOCATION "%Y-%m-%d_%H-%M-%S.ts" 
#define DEFAULT_FRAMES (4*60*25)

/* Filter signals and args */
enum
{
  /* FILL ME */
  LAST_SIGNAL
};

enum
{
  PROP_0,
  PROP_LOCATION,
  PROP_FRAMES
};

/* the capabilities of the inputs and outputs.
 *
 * describe the real formats here.
 */
static GstStaticPadTemplate sink_factory = GST_STATIC_PAD_TEMPLATE ("sink",
    GST_PAD_SINK,
    GST_PAD_ALWAYS,
    GST_STATIC_CAPS ("video/mpegts")
    );

#define gst_voc_schnipsel_sink_parent_class parent_class
G_DEFINE_TYPE (GstVocSchnipselSink, gst_voc_schnipsel_sink, GST_TYPE_ELEMENT);

static void gst_voc_schnipsel_sink_set_property (GObject * object, guint prop_id,
    const GValue * value, GParamSpec * pspec);
static void gst_voc_schnipsel_sink_get_property (GObject * object, guint prop_id,
    GValue * value, GParamSpec * pspec);
static gboolean gst_voc_schnipsel_sink_set_caps (GstBaseSink * sink,
    GstCaps * caps);
static gboolean gst_voc_schnipsel_sink_open_next_file (GstVocSchnipselSink *
    multifilesink);
static void gst_voc_schnipsel_sink_close_file (GstVocSchnipselSink * multifilesink,
    GstBuffer * buffer);
static gboolean gst_voc_schnipsel_sink_write_stream_headers (GstVocSchnipselSink * sink);

static gboolean gst_voc_schnipsel_sink_sink_event (GstPad * pad, GstObject * parent, GstEvent * event);
static GstFlowReturn gst_voc_schnipsel_sink_chain (GstPad * pad, GstObject * parent, GstBuffer * buf);

/* GObject vmethod implementations */

/* initialize the vocschnipselsink's class */
static void
gst_voc_schnipsel_sink_class_init (GstVocSchnipselSinkClass * klass)
{
  GObjectClass *gobject_class;
  GstElementClass *gstelement_class;
  GstBaseSinkClass *gstbasesink_class;

  gobject_class = (GObjectClass *) klass;
  gstelement_class = (GstElementClass *) klass;
  gstbasesink_class = (GstBaseSinkClass *) (klass);

  gstbasesink_class->set_caps = gst_voc_schnipsel_sink_set_caps;

  gobject_class->set_property = gst_voc_schnipsel_sink_set_property;
  gobject_class->get_property = gst_voc_schnipsel_sink_get_property;

  g_object_class_install_property (gobject_class, PROP_LOCATION,
      g_param_spec_string ("location", "Location", "Location of the file to write. Will be processed by strftime, so you can add date/time modifiers.",
          DEFAULT_LOCATION, G_PARAM_READWRITE));

  g_object_class_install_property (gobject_class, PROP_FRAMES,
      g_param_spec_uint64 ("frames", "Frames", "Number of frames sfter which a new File will be started. Defaults to 4*60*25 = 6000 Frames",
          0, G_MAXUINT64, DEFAULT_FRAMES, G_PARAM_READWRITE));

  gst_element_class_set_details_simple(gstelement_class,
    "VocSchnipselSink",
    "FIXME:Generic",
    "FIXME:Generic Template Element",
    "Peter Körner <<user@hostname.org>>");

  gst_element_class_add_pad_template (gstelement_class,
      gst_static_pad_template_get (&sink_factory));
}

/* initialize the new element
 * instantiate pads and add them to element
 * set pad calback functions
 * initialize instance structure
 */
static void
gst_voc_schnipsel_sink_init (GstVocSchnipselSink * sink)
{
  sink->sinkpad = gst_pad_new_from_static_template (&sink_factory, "sink");
  gst_pad_set_event_function (sink->sinkpad,
                              GST_DEBUG_FUNCPTR(gst_voc_schnipsel_sink_sink_event));
  gst_pad_set_chain_function (sink->sinkpad,
                              GST_DEBUG_FUNCPTR(gst_voc_schnipsel_sink_chain));
  gst_element_add_pad (GST_ELEMENT (sink), sink->sinkpad);

  sink->location = g_strdup (DEFAULT_LOCATION);
  sink->maxframes = DEFAULT_FRAMES;
  sink->frames = 0;
}

static void
gst_voc_schnipsel_sink_set_property (GObject * object, guint prop_id,
    const GValue * value, GParamSpec * pspec)
{
  GstVocSchnipselSink *sink = GST_VOCSCHNIPSELSINK (object);

  switch (prop_id) {
    case PROP_LOCATION:
      g_free (sink->location);
      sink->location = g_strdup (g_value_get_string (value));
      break;
    case PROP_FRAMES:
      sink->maxframes = g_value_get_uint64 (value);
      break;
    default:
      G_OBJECT_WARN_INVALID_PROPERTY_ID (object, prop_id, pspec);
      break;
  }
}

static void
gst_voc_schnipsel_sink_get_property (GObject * object, guint prop_id,
    GValue * value, GParamSpec * pspec)
{
  GstVocSchnipselSink *sink = GST_VOCSCHNIPSELSINK (object);

  switch (prop_id) {
    case PROP_LOCATION:
      g_value_set_string (value, sink->location);
      break;
    case PROP_FRAMES:
      g_value_set_uint64 (value, sink->maxframes);
      break;
    default:
      G_OBJECT_WARN_INVALID_PROPERTY_ID (object, prop_id, pspec);
      break;
  }
}

static gboolean
gst_voc_schnipsel_sink_set_caps (GstBaseSink * sink, GstCaps * caps)
{
  GstVocSchnipselSink *vocschnipselsink;
  GstStructure *structure;

  vocschnipselsink = GST_VOCSCHNIPSELSINK (sink);

  structure = gst_caps_get_structure (caps, 0);
  if (structure) {
    const GValue *value;

    value = gst_structure_get_value (structure, "streamheader");

    if (GST_VALUE_HOLDS_ARRAY (value)) {
      int i;

      if (vocschnipselsink->streamheaders) {
        for (i = 0; i < vocschnipselsink->n_streamheaders; i++) {
          gst_buffer_unref (vocschnipselsink->streamheaders[i]);
        }
        g_free (vocschnipselsink->streamheaders);
      }

      vocschnipselsink->n_streamheaders = gst_value_array_get_size (value);
      vocschnipselsink->streamheaders =
          g_malloc (sizeof (GstBuffer *) * vocschnipselsink->n_streamheaders);

      for (i = 0; i < vocschnipselsink->n_streamheaders; i++) {
        vocschnipselsink->streamheaders[i] =
            gst_buffer_ref (gst_value_get_buffer (gst_value_array_get_value
                (value, i)));
      }
    }
  }

  return TRUE;
}

/* GstElement vmethod implementations */

/* this function handles sink events */
static gboolean
gst_voc_schnipsel_sink_sink_event (GstPad * pad, GstObject * parent, GstEvent * event)
{
  gboolean ret;
  //GstVocSchnipselSink *filter;
  //filter = GST_VOCSCHNIPSELSINK (parent);

  switch (GST_EVENT_TYPE (event)) {
    case GST_EVENT_CAPS:
    {
      GstCaps * caps;

      gst_event_parse_caps (event, &caps);
      /* do something with the caps */

      /* and forward */
      ret = gst_pad_event_default (pad, parent, event);
      break;
    }
    default:
      ret = gst_pad_event_default (pad, parent, event);
      break;
  }
  return ret;
}

/* chain function
 * this function does the actual processing
 */
static GstFlowReturn
gst_voc_schnipsel_sink_chain (GstPad * pad, GstObject * parent, GstBuffer * buf)
{
  GstVocSchnipselSink *sink;
  sink = GST_VOCSCHNIPSELSINK (parent);

  GstMapInfo map;
  gst_buffer_map (buf, &map, GST_MAP_READ);

  if(++sink->frames > sink->maxframes)
  {
    sink->frames = 0;

    if (sink->file)
    {
        gst_voc_schnipsel_sink_close_file (sink, buf);
    }

    if (!gst_voc_schnipsel_sink_open_next_file (sink))
    {
      GST_ELEMENT_ERROR (sink, RESOURCE, WRITE,
        ("Error while writing to file."), ("%s", g_strerror (errno)));
      gst_buffer_unmap (buf, &map);
      return GST_FLOW_ERROR;
    }

    gst_voc_schnipsel_sink_write_stream_headers (sink);
  }

  if (sink->file == NULL) {
    if (!gst_voc_schnipsel_sink_open_next_file (sink))
    {
      GST_ELEMENT_ERROR (sink, RESOURCE, WRITE,
        ("Error while writing to file."), ("%s", g_strerror (errno)));
      gst_buffer_unmap (buf, &map);
      return GST_FLOW_ERROR;
    }
  }

  int ret = fwrite (map.data, map.size, 1, sink->file);
  if (ret != 1)
  {
    GST_ELEMENT_ERROR (sink, RESOURCE, WRITE,
      ("Error while writing to file."), ("%s", g_strerror (errno)));
    gst_buffer_unmap (buf, &map);
    return GST_FLOW_ERROR;
  }

  gst_buffer_unmap (buf, &map);
  return GST_FLOW_OK;
}


static gboolean
gst_voc_schnipsel_sink_write_stream_headers (GstVocSchnipselSink * sink)
{
  int i;

  if (sink->streamheaders == NULL)
    return TRUE;

  for (i = 0; i < sink->n_streamheaders; i++) {
    GstBuffer *hdr;
    GstMapInfo map;
    int ret;

    hdr = sink->streamheaders[i];
    gst_buffer_map (hdr, &map, GST_MAP_READ);
    ret = fwrite (map.data, map.size, 1, sink->file);
    gst_buffer_unmap (hdr, &map);

    if (ret != 1)
      return FALSE;
  }

  return TRUE;
}

static gboolean
gst_voc_schnipsel_sink_open_next_file (GstVocSchnipselSink * sink)
{
  char filename[250];

  g_return_val_if_fail (sink->file == NULL, FALSE);

  time_t rawtime;
  struct tm * timeinfo;
  time (&rawtime);
  timeinfo = localtime (&rawtime);

  strftime(filename, sizeof(filename)/sizeof(*filename), sink->location, timeinfo);
  printf("new file %s\n", filename);

  sink->file = fopen (filename, "wb");
  if (sink->file == NULL) {
    g_free (filename);
    return FALSE;
  }

  GST_INFO_OBJECT (sink, "opening file %s", filename);

  return TRUE;
}

static void
gst_voc_schnipsel_sink_close_file (GstVocSchnipselSink * sink,
    GstBuffer * buffer)
{
  fclose (sink->file);
  sink->file = NULL;
}




/* entry point to initialize the plug-in
 * initialize the plug-in itself
 * register the element factories and other features
 */
static gboolean
vocschnipselsink_init (GstPlugin * vocschnipselsink)
{
  /* debug category for fltering log messages
   *
   * exchange the string 'Template vocschnipselsink' with your description
   */
  GST_DEBUG_CATEGORY_INIT (gst_voc_schnipsel_sink_debug, "vocschnipselsink",
      0, "Template vocschnipselsink");

  return gst_element_register (vocschnipselsink, "vocschnipselsink", GST_RANK_NONE,
      GST_TYPE_VOCSCHNIPSELSINK);
}

/* PACKAGE: this is usually set by autotools depending on some _INIT macro
 * in configure.ac and then written into and defined in config.h, but we can
 * just set it ourselves here in case someone doesn't use autotools to
 * compile this code. GST_PLUGIN_DEFINE needs PACKAGE to be defined.
 */
#ifndef PACKAGE
#define PACKAGE "myfirstvocschnipselsink"
#endif

/* gstreamer looks for this structure to register vocschnipselsinks
 *
 * exchange the string 'Template vocschnipselsink' with your vocschnipselsink description
 */
GST_PLUGIN_DEFINE (
    GST_VERSION_MAJOR,
    GST_VERSION_MINOR,
    vocschnipselsink,
    "Template vocschnipselsink",
    vocschnipselsink_init,
    VERSION,
    "LGPL",
    "GStreamer",
    "http://gstreamer.net/"
)
